Please read the README.md on github if possible

Email Service - for the Uber coding challenge

This is one of the Uber coding challenge project.

The problem:

Create a service that accepts the necessary information and sends emails.
It should provide an abstraction between two different email service providers.
If one of the services goes down, your service can quickly fail over to a different provider without affecting your customers.

The solution:

I create a service(focus on backend) that sends the email to the recipient by taking the emails of recipient and sender,
the subject and content as inputs. It is backed by Mailgun and Mandrill. It always try to use Mandrill first,
and if there's anything wrong, it tried to use Mailgun to send the email.

live site : http://lovekc.pythonanywhere.com/

Installation/Deployment

Install virtualenv if needed
Install Python dependencies by: pip install -r requirements.txt
Put the mandrill API key, mailgun API key and the base API url into the config.py file. You can get those by creating free account on mandrill and mailgun
You can run it locally by python view.py and you can access it on http://127.0.0.1:5000/


Usage

You can use the live site or make a post to the / end point directly.

e.g.


import requests

message = {
    'to_email': 'dawen.uiuc@gmail.com',
    'from_email': 'youremail@gmail.com',
    'subject': 'subject ',
    'content': 'plain text content to send '
    }

r = requests.post('http://lovekc.pythonanywhere.com/', message)
print r.message

# r is the result object that that contains status, status_code and message

Note:

the email may not send immediately, it could be just queue by by Mandrill or Mailgun
the status_code will be 200 if there's nothing wrong otherwise it will be 400
Mandrill may return "rejected" status, e.g. one of the case could be the to_email is in the black list in their system. If Mandrill return "rejected" status, it will try to use Mailgun to send the email, if that also fails, will return "rejected" status and message about the reject reason
Testing

All the tests are inside tests.py, run all of them by : python tests.py

Development

Design

I implemented a abstract base class to define a interface for email providers. Each email provider is a subclass of the base class, and they all implement the send method. It's flexible to add more providers and add more methods in each provider. However, I didn't implement a complex logic around how to choose which email provider to use and queue up the email sending tasks so that the distributed tasks could be executed asynchronously. I think it's overkill for the purpose of this project and I don't have enough time to do that, but with the current design, it's flexible to do that.

Technical Choices

Back-end

    Python. I choose Python because I have some basic knowledge about it although I haven't written any Python code for more than 1 year,
        but more important is that Python (or ruby) is really suitable for this task.
        In contrast, using Java with Spring, for example, is overkill and it's much harder to set up development environment.

    Flask. Although I don't have any experience with this framework, but comparing to Django and Pyramid,
    Flask is pretty lightweight and easy to use.

Front-end

Didn't spend lot time on Front-end, I create the from using pFrom and modify the html and css a bit.

Improvements(If spending additional time on the project)

Add more features: support cc (multiple recipients), support html content and attachments.
Depend on the use cases, The email sending tasks could be distributed and executed asynchronously to get better performance.
Implement a endpoint to track the emails are sent/ not sent.
Improve the UI, make it more user friendly, maybe use WTForms or javascript to do some validations on the email form.

About me

https://www.linkedin.com/in/dawenhuang