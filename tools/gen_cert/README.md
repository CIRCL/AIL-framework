Usage
=====
These scripts are useful to generate the server's self-signed certificate.
## Root Certification Authority ##
`gen_root.sh`
This will create a rootCA.crt to verify the server's cert.
## Server certificate ##
### Configuration Files ###
Look into these files if you plan to verify the certificate:
  * san.cnf holds basic information about the certificate.
  * ext.3 holds in particular the 'subjectAltNames** option that is for the verification to succeed.

 ### Generation ###
`gen_root.sh`
