import os
import json
import base64
from datetime import datetime,timedelta

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
       
        print('success')
