# cfut - cli wrapper for aws cloudformation

Invoking "aws cloudformation" gets tedious after a while because the commands are 
pretty verbose, stack names can be long etc.

This utility creates a cfut.json in your working directory, and allows you to
refer to stacks with aliases.

Installation:

```
$ pip install cfut

# Optional bonus to make 'cfut lint' work:

$ pip install cfn-lint 
```

Example use (first time):

```
PS C:\t\tt> cfut
Config file cfut.json not found, create it in C:\t\tt [y/n]? y
Run cfut -h to get help.
Workspace: C:\t\tt
default: hummaa_template.yml => hummaa_template
PS C:\t\tt> cfut -h
usage: cfut [-h] {init,lint,update,create,describe,res,delete,ls} ...

positional arguments:
  {init,lint,update,create,describe,res,delete,ls}
    init                Initialize working directory
    lint                Lint templates
    update              Call with template: update-stack
    create              Call with template: create-stack
    describe            Call: describe-stacks
    res                 Call: describe-stack-resources
    delete              Call: delete-stack
    ls                  Alias: describe-stacks

optional arguments:
  -h, --help            show this help message and exit

```

Example cfut.json config file:

```
{
  "profile": "default",
  "templates": {
    "default": {
      "name": "hummaa_template",
      "path": "hummaa_template.yml",
      "capabilities": ["CAPABILITY_NAMED_IAM"],
      "parameters": null
    }
  }
}
```