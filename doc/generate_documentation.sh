DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
epydoc -o $DIR --debug --parse-only --graph all -v pln_inco
#epydoc -o $DIR --debug -v pln_inco

