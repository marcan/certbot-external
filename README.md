## External shell script plugin for Let's Encrypt client

This plugin allows you to use a custom shell script to implement DVSNI
validation for your domains. It should work with any conceivable server that
supports TLS and SNI, and can also be used to perform DVSNI validation using
a server (e.g. a web server) that is unrelated to the server that will be using
the certificate (e.g. a mail server), as long as both share the same external
IP address.

The [example external-handler.sh](external-handler.sh.example) supports DVSNI
validation using nginx, in a setup where `/etc/nginx/sites.d` contains
configuration files for each site. No existing configuration files are edited;
instead, a new site config for the DVSNI challenge is created and then removed.

To install, first install let's encrypt (either on the root or in a virtualenv),
then:

    # python setup.py install
    # cp external-handler.sh.example /etc/letsencrypt/external-handler.sh
    # chmod +x /etc/letsencrypt/external-handler.sh

To use, try something like this:

    # certbot --agree-tos --agree-dev-preview \
        -a certbot-external:external \
        -d example.com certonly

This plugin only supports authentication, not installation, since it is assumed
that the administrator will install the certificate manually. It can be used
with the renewer too, but you'll have to wrap it with a script that checks
whether any certificates were renewed and restarts the appropriate server(s) if
needed.

Loosely based on the Let's Encrypt nginx plugin.
