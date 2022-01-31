# Cisco Configuration Validator

ConfParser by https://github.com/tdorssers/confparser <br>
builder.py requires the input policy map name to be input based on customer requirements
<br>
# Builder (.py)

Builder will take values from the core switch and generate access switch configuration based on templates.  If the SVI is not on the core switch, the configuration on the access switch interface will differ slightly (NAC rules).

# Diff Generator (.py)

The difference generator is used to highlight configuraiton changes between two versions (of the same switch).  It's typically used during a go live phase to ensure any changes to the configuration are found before the cutover.
