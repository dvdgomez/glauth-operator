# Glauth Operator

Glauth provides a lightweight LDAP server with configurable backends.

This operator builds a simple deployment of the Glauth server and provides a relation interface such
that it can be integrated with other Juju charms in a model.

## Usage

You can deploy the operator as such:

```shell
# Deploy the charm
$ juju deploy glauth --channel edge
```