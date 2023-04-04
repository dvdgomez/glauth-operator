# Glauth Operator

Glauth provides a lightweight LDAP server with configurable backends.

This operator builds a simple deployment of the Glauth server and provides a relation interface such
that it can be integrated with other Juju charms in a model.

## Usage

You can deploy the operator as such:

```shell
# Deploy the charm with a resource
$ juju deploy glauth --channel edge --resource config=config.zip

# Deploy the charm with no resource
$ juju deploy glauth --channel edge
```

## Configuration

In order for glauth to properly integrate with SSSD its configuration must be configured.

```shell
# LDAP domain
juju config glauth domain=MYDOMAIN

# ldap_default_bind_dn
juju config glauth ldap-default-bind-dn=cn=serviceuser,ou=svcaccts,dc=glauth,dc=com

# ldap_default_authtok
juju config glauth ldap-password=mysecret

# ldap_search_base
juju config glauth ldap-search-base=dc=glauth,dc=com
```

The GLAuth configuration can be passed in as a resource in a *.zip. If no resource is used then a default configuration is created with no users. 

## Integrations

The glauth-operator can integrate with the sssd-operator over the ldap-client integration.

```shell
juju integrate glauth:ldap-client sssd:ldap-client
```