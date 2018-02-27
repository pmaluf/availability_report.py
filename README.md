# availability_report.py

This script generate an availability report of sensu alarms stored on Elasticsearch

## Notice

This script was tested in:

* Linux
  * OS Distribution: CentOS release 6.7 (Final)
  * Python: 2.7

## Prerequisities

* Python Modules
  * elasticsearch
  * pandas

## How to use it

```
./availability_report.py --help
usage: availability_report.py [-h] [-H HOST] [-P PORT] [-s START_DATE]
                              [-e END_DATE] [-c]

optional arguments:
  -h, --help            show this help message and exit
  -H HOST, --elastic-host HOST
                        The elasticsearch you want to connect to
  -P PORT, --port PORT  The port elasticsearch is running on
  -s START_DATE, --start-date START_DATE
                        The start date of report. (YYYY-MM-DD)
  -e END_DATE, --end-date END_DATE
                        The end time of report. (YYYY-MM-DD)
  -c, --csv             Output in csv format

```

Example:
```
./availability_report.py --start-date 2018-01-01 --end-date 2018-01-15

                                                    Alarms  Downtime  Availability
Check_name                                                                        
BRM-CONNECTION_BRM-APP-1                                 5      1005     99.955072
BRM-CONNECTION_BRM-APP-2                                 3     27540     98.768825
BRM-CONNECTION_BRM-APP-3                                 7      4380     99.804192
CHECK-DW-MALHA-1_DW-1                                   24    287281     87.157113
CHECK-DW-MALHA-2_DW-1                                    1     19082     99.146940
CHECK-NONO-DIGITO_NONO-DIGITO-1                          1       360     99.983906
CHECK-WAY-EXTRACTOR-APP-LOG_WAY-...                     21     93961     95.799477
CHECK-WAY-EXTRACTOR-SERVICE-WAY...                      21     95042     95.751151
CHECK-SYNCREPL_LDAP-INFRA-1                              4     33795     98.489196
CHECK-SYNCREPL_LDAP-INFRA-2                              4     33857     98.486424
CHECK-SYNCREPL_LDAP-INFRA-3                              4     33823     98.487944
CHECK-WINDOWS-RAM_EDUCA-WEB-1                            1   1953381     12.674171
CHECK-WINDOWS-RAM_STG-CORE-2                             1        63     99.997184
CHECKDISK_BFF-ROBO-1                                     1    570619     74.490498
CHECKDISK_DISCO-SOLR-A-01                                1   1704061     23.820012
CHECKDISK_DISCO-SWIFT-B-19                               1   2164356      3.242541
CHECKDISK_APIWEB-1                                       5     37624     98.318020
CHECKDISK_APIWEB-3                                       1   1594796     28.704700
CHECKDISK_PUPPET-CI-1                                    2     20041     99.104068
CHECKFSTAB_MOUNTS_DISCO-METADATA-A-02                    1      3780     99.831015
CHECKFSTAB_MOUNTS_DISCO-SOLR-A-01                        1   1704084     23.818984
```

## License

This project is licensed under the MIT License - see the [License.md](License.md) file for details
