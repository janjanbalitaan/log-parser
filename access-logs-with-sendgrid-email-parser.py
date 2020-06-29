import os
import json
import base64
from datetime import datetime,timedelta

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition, ContentId

def send_email(sendgrid_client, message):
    try:
        response = sendgrid_client.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
        print('Successful sending of email')
    except Exception as e:
        print(e.message)

def get_sendgrid_client(api_key):
    try:
        sendgrid_client = SendGridAPIClient(api_key)

        return sendgrid_client
    except:
        return None

def set_email_message(senders, recipients, subject, content):
    try:
        message = Mail(
                from_email=senders,
                to_emails=recipients,
                subject=subject,
                html_content=content
                )
        return message
    except:
        return None

def set_email_attachment(filename, encoded):
    try:
        attachment = Attachment()
        attachment.file_content = FileContent(encoded)
        attachment.file_type = FileType('text/csv')
        attachment.file_name = FileName(filename)
        attachment.disposition = Disposition('attachment')
        attachment.content_id = ContentId(filename)

        return attachment
    except:
        return None

def get_encoded_file(filepath):
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
            f.close()

        encoded = base64.b64encode(data).decode()

        return encoded
    except:
        return None

if __name__ == '__main__':
    access_log_date = (datetime.now() - timedelta(days=1)).strftime(os.environ['DATE_FORMAT'])
    in_filepath = '{path}{name}'.format(path=os.environ['ACCESS_LOG_PATH'], name=os.environ['ACCESS_LOG_FILE_FORMAT'].format(date=access_log_date))
    out_filename = os.environ['WRITE_FILE_FORMAT'].format(date=access_log_date)
    out_filepath = '{path}{name}'.format(path=os.environ['WRITE_FILE_PATH'], name=out_filename)

    with open(in_filepath) as f:
        data = {}
        for line in f:
            if 'str' in line:
                break

            row = line.split(' ')

            http_resource = row[5]
            http_code = row[6]
            http_time = row[8]

            if http_resource not in data:
                sub_data = {'http_codes': [http_code], 'http_elapsed_time': [http_time.replace('\n', '')]}
                data[http_resource] = sub_data
            else:
                http_codes = data[http_resource]['http_codes']
                http_codes.append(http_code)
                http_elapsed_time = data[http_resource]['http_elapsed_time']
                http_elapsed_time.append(http_time.replace('\n', ''))
                sub_data = {'http_codes': http_codes, 'http_elapsed_time': http_elapsed_time}
                data[http_resource] = sub_data

        with open(out_filepath, 'w+') as fout:
            for resource in data:
                http_codes_dict = {}
                http_codes = data[resource]['http_codes']
                http_times = data[resource]['http_elapsed_time']

                for http_code in http_codes:
                    
                    if http_code not in http_codes_dict:
                        http_codes_dict[http_code] = 1
                    else:
                        http_codes_dict[http_code] += 1
                    
                count = 0
                high = 0
                low = 0
                total = 0
                for http_time in http_times:
                    t = float(http_time)
                    if count == 0:
                        low = t

                    if t > high:
                        high = t
                    
                    if t < low:
                        low = t

                    total += t
                    count += 1
                
                avg = total / count

                fout.write('HTTP Resource: ' + resource + '\n')
                fout.write('Number of Hits: ' + str(count) + '\n')
                fout.write('Slowest Time: ' + str(high) + '\n')
                fout.write('Fastest Time: ' + str(low) + '\n')
                fout.write('Average Time: ' + str(avg) + '\n')
                fout.write('HTTP Codes:')
                for code in http_codes_dict:
                    fout.write(code + ': ' + str(http_codes_dict[code]) + '\n')
        
        encoded = get_encoded_file(out_filepath)
        if encoded is None:
            print('Can\'t encode the file')
        else:
            attachment = set_email_attachment(out_filename, encoded)

            if attachment is None:
                print('Can\'t attach file')
            else:
                email_to = os.environ['EMAIL_TO']
                email_from = os.environ['EMAIL_FROM']
                email_subject = os.environ['EMAIL_SUBJECT'] + ' (' + access_log_date + ')'
                email_content = os.environ['EMAIL_CONTENT']
                senders = email_from
                recipients = email_to
                message = set_email_message(senders, recipients, email_subject, email_content)
                if message is None:
                    print('Can\'t create an email message')
                else:
                    message.attachment = attachment
                    email_key = os.environ['EMAIL_KEY']
                    sendgrid_client = get_sendgrid_client(email_key)
                    if sendgrid_client is None:
                        print('Can\'t create a sendgrid client')
                    else:
                        send_email(sendgrid_client, message)
