
/*
    Test Rule
*/

rule certificatestest
{
    strings:
        $ssh_priv = "BEGIN RSA PRIVATE KEY" wide ascii nocase
        $pem_cert = "BEGIN CERTIFICATE" wide ascii nocase

    condition:
        any of them
}
