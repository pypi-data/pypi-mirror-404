[![penterepTools](https://www.penterep.com/external/penterepToolsLogo.png)](https://www.penterep.com/)


## PTGRAPHQL

PTGRAPHQL is a security testing tool for identifying vulnerabilities in GraphQL instances

## Installation

```
pip install ptgraphql
```

## Adding to PATH
If you're unable to invoke the script from your terminal, it's likely because it's not included in your PATH. You can resolve this issue by executing the following commands, depending on the shell you're using:

For Bash Users
```bash
echo "export PATH=\"`python3 -m site --user-base`/bin:\$PATH\"" >> ~/.bashrc
source ~/.bashrc
```

For ZSH Users
```bash
echo "export PATH=\"`python3 -m site --user-base`/bin:\$PATH\"" >> ~/.zshrc
source ~/.zshrc
```

## Usage examples
```
ptgraphql -u htttps://www.example.com/
```

## Options
```
   -u   --url         <url>               Connect to URL
   -p   --proxy       <proxy>             Set proxy (e.g. http://127.0.0.1:8080)
   -ts  --tests       <test>              Specify one or more tests to perform:
                       IS_GRAPHQL         GraphQL availability test
   -t   --threads     <threads>           Set thread count (default 10)
   -T   --timeout                         Set timeout (default 10)
   -c   --cookie      <cookie>            Set cookie
   -a   --user-agent  <a>                 Set User-Agent header
   -vv  --verbose                         Enable verbose mode
   -w   --wordlist    <path/to/wordlist>  Specify wordlist to bruteforce GraphQL endpoint. Default: data/wordlists/endpoints.txt
   -H   --headers     <header:value>      Set custom header(s)
   -r   --redirects                       Follow redirects (default False)
   -C   --cache                           Cache HTTP communication (load from tmp in future)
   -v   --version                         Show script version and exit
   -h   --help                            Show this help message and exit
   -j   --json                            Output in JSON format

```

## Dependencies
```
ptlibs
```

## License

Copyright (c) 2025 Penterep Security s.r.o.

ptgraphql is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

ptgraphql is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with ptgraphql. If not, see https://www.gnu.org/licenses/.

## Warning

You are only allowed to run the tool against the websites which
you have been given permission to pentest. We do not accept any
responsibility for any damage/harm that this application causes to your
computer, or your network. Penterep is not responsible for any illegal
or malicious use of this code. Be Ethical!