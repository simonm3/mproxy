Modules
=======

Manager - rotates proxies
Proxy (AWS, AWSNord, Tor) - proxy server
source (google, translate) - function to get data
Task - wraps a source to capture ProxyException and maintain session.

Installing tor as a service on windows
======================================

To use tor with python/stem it must be installed as a service. Take care with these instructions as mistakes fail silently::

    open powershell in admin mode
    install tor into c:/ NOT program files as need write permissions

    cd "C:\Tor Browser\Browser\TorBrowser\tor"
    tor --hash-password <password> | more
    edit data/torrc to add "HashedControlPassword <hashed password>"
    tor --service install -options ControlPort 9151

Many websites (e.g. google) block or require captcha for all tor exit nodes

Monthly costs
=============

Blazing Proxies (min 5)
shared US       50c =====> $2.50 for 5
dedicated US    $1.20
dedicated UK    $2

AWS             1c/hour => $7.20
NordVPN         $3.50 + AWS cost
Tor             0





