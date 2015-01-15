from simple_email import MandrillEmail, MailgunEmail, simple_validate_send_request
from view import app
from mandrill import ValidationError
import unittest, mock

valid_message = {
    'to_email': 'dawen.uiuc@gmail.com',
    'from_email': 'uber@gmail.com',
    'subject': 'here is a  subject ',
    'content': 'content to send '
    }

message_with_empty_to_email = {
    'to_email': '',
    'from_email': 'uber@gmail.com',
    'subject': 'email subject ',
    'content': 'content'
    }

message_with_invalid_to_email = {
    'to_email': 'xx',
    'from_email': 'uber@gmail.com',
    'subject': 'email subject ',
    'content': 'content'
    }

message_with_empty_from_email = {
    'to_email': 'dawen.uiuc@gmail.com',
    'from_email': '',
    'subject': 'email subject ',
    'content': 'content'
    }

message_with_invalid_from_email = {
    'to_email': 'dawen.uiuc@gmail.com',
    'from_email': 'Uber',
    'subject': 'email subject ',
    'content': 'content'
    }

message_with_empty_content = {
    'to_email': 'dawen.uiuc@gmail.com',
    'from_email': 'uber@gmail.com',
    'subject': 'email subject',
    'content' : ''
    }


message_with_empty_subject = {
    'to_email': 'dawen.uiuc@gmail.com',
    'from_email': 'uber@gmail.com',
    'subject': '',
    'content': 'content with no subject to send '
    }


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_post(self):

        result = self.app.post('/', data=valid_message)
        assert result.status_code == 200
        assert "Email sent successfully!" in result.data


    def test_send_email_error(self):
        result = self.app.post('/', data=message_with_empty_to_email)
        assert "invalid recipient email" in result.data

        result = self.app.post('/', data=message_with_invalid_to_email)
        assert "invalid recipient email" in result.data

        result = self.app.post('/', data=message_with_empty_from_email)
        assert "invalid sender email" in result.data

        result = self.app.post('/', data=message_with_invalid_from_email)
        assert "invalid sender email" in result.data

        result = self.app.post('/', data=message_with_empty_subject)
        assert "subject cannot be empty" in result.data

        result = self.app.post('/', data=message_with_empty_content)
        assert "content cannot be empty" in result.data


class MailgunAndMandrillTests(unittest.TestCase):

    def test_mailgun_send(self):
        result = MailgunEmail().send(valid_message)
        assert_success_result(result)

        result = MailgunEmail().send(message_with_empty_subject)
        assert_success_result(result)

    def test_mailgun_send_error(self):
        result = MailgunEmail().send(message_with_empty_to_email)
        assert_error_result(result, "'to' parameter is not a valid address. please check documentation")

        result = MailgunEmail().send(message_with_invalid_from_email)
        assert_error_result(result, "'from' parameter is not a valid address. please check documentation")

        result = MailgunEmail().send(message_with_invalid_to_email)
        assert_error_result(result, "'to' parameter is not a valid address. please check documentation")

        result = MailgunEmail().send(message_with_empty_from_email)
        assert_error_result(result, "'from' parameter is not a valid address. please check documentation")

        result = MailgunEmail().send(message_with_empty_content)
        assert_error_result(result, "Need at least one of 'text' or 'html' parameters specified")


    @mock.patch("simple_email.mandrill_client.messages.send")
    def test_mandrill_send(self, send):
        send.side_effect = success_response_side_effect()
        result = MandrillEmail().send(valid_message)
        assert_success_result(result)

    @mock.patch("simple_email.mandrill_client.messages.send")
    def test_mandrill_send_error(self, send):

        send.side_effect = empty_to_email_side_effect()
        result = MandrillEmail().send(message_with_empty_to_email)
        assert_error_result(result, mandrill_empty_to_email_validation_error)

        send.side_effect = invalid_from_email_side_effect()
        result = MandrillEmail().send(message_with_invalid_from_email)
        assert_error_result(result, mandrill_invalid_from_email_validation_error)

        send.side_effect = invalid_to_email_side_effect()
        result = MandrillEmail().send(message_with_invalid_to_email)
        assert_error_result(result, "Get an unexpected status from Mandrill!", 'invalid')

        send.side_effect = empty_from_email_side_effect()
        result = MandrillEmail().send(message_with_empty_from_email)
        assert  result.status_code == 400
        assert result.status == 'rejected'
        assert 'invalid-sender' in result.message


def test_simple_validate_send_request():
    assert None == simple_validate_send_request(valid_message)
    assert 'invalid recipient email' == simple_validate_send_request(message_with_empty_to_email).message
    assert 'invalid recipient email' == simple_validate_send_request(message_with_invalid_to_email).message
    assert 'invalid sender email' == simple_validate_send_request(message_with_empty_from_email).message
    assert 'invalid sender email' == simple_validate_send_request(message_with_invalid_from_email).message
    assert 'subject cannot be empty' == simple_validate_send_request(message_with_empty_subject).message
    assert 'content cannot be empty' == simple_validate_send_request(message_with_empty_content).message


def success_response_side_effect():
    return [[{u'status': u'sent', u'_id': u'857366672c72487eb94fb5ce3f3675d3', u'email': u'dawen.uiuc@gmail.com', u'reject_reason': None}]]


def empty_from_email_side_effect():
    return [[{u'status': u'rejected', u'_id': u'cd7ed450113d4c608f4101eef3748a3c', u'email': u'dawen.uiuc@gmail.com', u'reject_reason': u'invalid-sender'}]]


def invalid_to_email_side_effect():
    return [[{"email":"xx@","status":"invalid","_id":"da0b5b7d506046789a75bbf2f7284132","reject_reason": None}]]

mandrill_empty_to_email_validation_error = 'Validation error: {"message":{"to":[{"email":"Sorry, this field can\'t be left blank."}]}}!'


def empty_to_email_side_effect():
    return ValidationError(mandrill_empty_to_email_validation_error)

mandrill_invalid_from_email_validation_error = 'Validation error: {"message":{"from_email":"An email address must contain a single @"}}'


def invalid_from_email_side_effect():
    return ValidationError(mandrill_invalid_from_email_validation_error)


def assert_error_result(result, message, status="error"):
    assert result.message == message
    assert result.status_code == 400
    assert result.status == status


def assert_success_result(result, message="Email sent successfully!"):
    assert result.message == message
    assert result.status_code == 200
    assert result.status == "success"


test_case = unittest.FunctionTestCase(test_simple_validate_send_request)

if __name__ == '__main__':
    test_suite = unittest.TestSuite()
    test_suite.addTest(test_case)
    unittest.TextTestRunner().run(test_suite)
    unittest.main()