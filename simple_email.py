
from __future__ import print_function
from validate_email import validate_email
from abc import ABCMeta, abstractmethod
import mandrill, logging, requests, config
mandrill_client = mandrill.Mandrill(config.MANDRILL_API_KEY)


class Result(object):
    # standardize the results from Mandrill and Mailgun
    def __init__(self, status, message, status_code=400):
        self.status_code = status_code
        self.status = status
        self.message = message


class SuccessResult(Result):
    def __init__(self, message, status_code=200):
        super(type(self), self).__init__("success", message, status_code)


class ErrorResult(Result):
    def __init__(self, message, status_code=400):
        super(type(self), self).__init__("error", message, status_code)


logger = logging.getLogger('simple_email')
logger.setLevel(logging.INFO)
fh = logging.FileHandler('error.log')
fh.setLevel(logging.ERROR)
logger.addHandler(fh)


MAX_SUBJECT_LENGTH = 1000
MAX_CONTENT_LENGTH = 10000

success_result_obj = SuccessResult("Email sent successfully!")


def send_email(message_data):
    result = simple_validate_send_request(message_data)
    if result is not None:
        return result

    '''
    It's flexible to use task queue to makes asynchronous execution of email sending tasks
    but I think it's overkill overkill for the purpose of this project and I don't have enough time to do that.
    Here, it always try to use Mandrill to send the email first, and if there's something
    wrong like Mandrill service is down, it will try to use Mailgun to send the email.
    Note that the email may not send immediately, it could be just queue by by Mandrill or Mailgun
    During the testing, Mailgun sometime has notable delays.
    '''
    mandrill_result = MandrillEmail().send(message_data)
    if mandrill_result.status == "success":
        logger.debug("Returning result from mandrill:: status: %s, message: %s  " % (mandrill_result.status, mandrill_result.message))
        return mandrill_result

    mailgun_result = MailgunEmail().send(message_data)

    if mailgun_result.status == "success":
        logger.debug("Returning result from mailgun:: status: %s, message %s " % (mailgun_result.status, mailgun_result.message))
        return mailgun_result

    if mailgun_result.status == "rejected":
        logger.debug("Returning result from mandrill:: status: %s, message: %s  " % (mandrill_result.status, mandrill_result.message))
        return mandrill_result

    return ErrorResult("Sorry! We cannot send email for now. Please try later.")


class SimpleEmail(object):
    __metaclass__ = ABCMeta

    def __init__(self, debug = False):
        if debug:
            logger.handlers = []
            logger.addHandler(logging.StreamHandler())
            logger.setLevel(logging.DEBUG)

    @abstractmethod
    def send(self, message):
        pass


class MailgunEmail(SimpleEmail):

    def send(self, message_data):
        ''' Send email using Mailgun

        Args:
           message_data : contains the information about the email will be sent::
                from_email (string): the sender email address.
                to_email (string): the email address of the recipient (only have one recipient for now)
                content (string): full text content to be sent
                subject (string): the message subject (optional)

        Returns:
            a SuccessResult object for success and a ErrorResult object for failure

        Note: With the current setup, responses with 400 error code will not be returned since Mailgun returns 400 error only when there's a
              invalid email or empty content but we already done validation before calling this method.

              Changing this function e.g. adding new email parameters may cause 400 error, so make sure to check the official documentation of
              Mailgun to see if it will return 400 error and handle them correctly.

              All errors are caught and the responses are logged
        '''


        logger.debug("Starting to call Mailgun to send the email")
        r = requests.post(
            config.MAILGUN_MESSAGE_BASE_URL,
            auth=("api", config.MAILGUN_API_KEY),
            data={"from": message_data['from_email'],
                  "to": message_data['to_email'],
                  "subject": message_data['subject'],
                  "text": message_data['content']})
        status_code = r.status_code
        json_response = r.json()
        response_message = json_response['message']
        logger.debug("Getting result from calling Mailgun: response code: %s, message: %s " % (status_code,response_message))
        if status_code == 200:
            return success_result_obj
        else:
            logger.error("Getting an error from Mailgun: response code: %s, message: %s " % (status_code,response_message))
        return ErrorResult(response_message, status_code)



class MandrillEmail(SimpleEmail):

    def send(self, message_data):
        ''' Send email using mandrill client lib

        Args:
            message_data : contains the information about the email will be sent::
                from_email (string): the sender email address.
                to_email (string): the email address of the recipient (only have one recipient for now)
                content (string): full text content to be sent (optional)
                subject (string): the message subject (optional)

        Returns:
            a SuccessResult object for success and a ErrorResult object for failure
            For the failure case, the object is generated based on
            the return results from Mandrill:
                array.  of structs for each recipient containing the key "email" with the email address, and details of the message status for that recipient::
                    [] (struct): the sending results for a single recipient::
                        [].email (string): the email address of the recipient
                        [].status (string): the sending status of the recipient - either "sent", "queued", "scheduled", "rejected", or "invalid"
                        [].reject_reason (string): the reason for the rejection if the recipient status is "rejected" - one of "hard-bounce", "soft-bounce", "spam", "unsub", "custom", "invalid-sender", "invalid", "test-mode-limit", or "rule"
                        []._id (string): the message's unique id

        Note: With the current setup, ValidationError will not be raised since
              Mandrill raises the ValidationError only when :
                * to_email is empty,
                * from_email has invalid email address format

              but we validate to_email and from_email before calling this method. Also, there will be no results with "invalid" or "queued" status
              returned since the from_email we pass will be always valid and we are not using the Mandrill schedule feature(async=False).

              The returned status will be invalid when:
                * to_email has invalid email address format

              and the returned status will be rejected and the reject reason  will be invalid-sender when:
                * from_email is empty

              Changing this function e.g. adding new email parameters may cause ValidationError or other errors, so make sure
              to check the official documentation of Mandrill to see if it will raise ValidationError or other errors and
              handle them correctly.

              We catch all the Mandrill Errors and log them
        '''

        message = {
            'from_email': message_data['from_email'],
            'subject': message_data['subject'],
            'text': message_data['content'],
            'to': [{'email': message_data['to_email'],
                    'type': 'to'}]
        }
        results = None
        try:
            logger.debug("Starting to call Mandrill to send the email")
            results = mandrill_client.messages.send(message=message, async=False, ip_pool='Main Pool')
            logger.debug("Get result back from Mandrill: %s " % results)
        except mandrill.Error as e:
            # Catch all Mandrill errors
            logger.exception("Get an exception when calling Mandrill to send the email!")
            return ErrorResult(e.message)

        result = results[0]
        if result['status'] == 'sent':
            return success_result_obj
        elif result['status'] == 'rejected':
            return Result(result['status'], "email to %s was rejected due to %s " % (result['email'], result['reject_reason']))
        else:
            logger.error("Get an unexpected status:  %s when calling Mandrill to send the email!" % result['status'])
            return Result(result['status'], "Get an unexpected status from Mandrill!")


def simple_validate_send_request(message_data):
    if not validate_email(message_data['to_email']):
        return ErrorResult("invalid recipient email")
    if not validate_email(message_data['from_email']):
        return ErrorResult("invalid sender email")
    if message_data['subject'] == "":
        return ErrorResult("subject cannot be empty")
    elif len(message_data['subject']) > MAX_SUBJECT_LENGTH:
        return ErrorResult("subject cannot be longer than" + MAX_SUBJECT_LENGTH)
    if message_data['content'] == "":
        return ErrorResult("content cannot be empty")
    elif len(message_data['content']) > MAX_CONTENT_LENGTH:
        return ErrorResult("content cannot be longer than" + MAX_CONTENT_LENGTH)

