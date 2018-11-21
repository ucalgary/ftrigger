#!/bin/sh
#   Use this script to test if a given TCP host/port or URL are available

cmdname=$(basename $0)

echoerr() { if [ ${QUIET} -ne 1 ]; then echo "$@" 1>&2; fi }

usage()
{
	cat << USAGE >&2
Usage:
    ${cmdname} host:port [-s] [-t timeout] [-- command args]
    -h HOST                     Host or IP under test
    -p PORT                     TCP port under test
    -u URL                      URL to test for success
    -U username                 If -u given, the username to authenticate with.
    -P password                 If -u given, the username's password to authenticate with.
    -r retry_time               Length of time between retries. Default 5.
    -s                          Only execute subcommand if the test succeeds
    -S                          Execute subcommand regardless of test succeeds (default)
    -q                          Do not output any status messages
    -t TIMEOUT                  Timeout in seconds, zero for no timeout
    -- COMMAND ARGS             Execute command with args after the test finishes
USAGE
    exit 1
}

wait_for()
{
    if [ -z "$URL" ]; then
	    if [ ${TIMEOUT} -gt 0 ]; then
		    echoerr "${cmdname}: waiting ${TIMEOUT} seconds for ${HOST}:${PORT}"
	    else
		    echoerr "${cmdname}: waiting without a timeout for ${HOST}:${PORT}"
	    fi
	    start_ts=$(date +%s)
	    while :; do
		    if [ ${ISBUSY} -eq 1 ]; then
			    nc -z ${HOST} ${PORT}
			    result=$?
		    else
			    (echo > /dev/tcp/${HOST}/${PORT}) >/dev/null 2>&1
			    result=$?
		    fi
		    if [ ${result} -eq 0 ]; then
			    end_ts=$(date +%s)
			    echoerr "${cmdname}: ${HOST}:${PORT} is available after $((end_ts - start_ts)) seconds"
			    break
		    fi
		    sleep ${RETRY_TIME}
	    done
    else
	    if [ ${TIMEOUT} -gt 0 ]; then
		    echoerr "${cmdname}: waiting ${TIMEOUT} seconds for ${URL}"
	    else
		    echoerr "${cmdname}: waiting without a timeout for ${URL}"
	    fi
	    start_ts=$(date +%s)
        if [ -n "${USERNAME}" ]; then
            AUTH="-u ${USERNAME}:${PASSWORD}"
        fi
        result=1
	    while :; do
            response_code=$(curl -s -o /dev/null -H 'Cache-Control: no-cache' -k -w '%{response_code}' ${AUTH} -k ${URL})
		    if [ ${response_code} -eq 200 ]; then
                result=0
			    end_ts=$(date +%s)
			    echoerr "${cmdname}: ${URL} is available after $((end_ts - start_ts)) seconds"
			    break
		    fi
		    sleep ${RETRY_TIME}
	    done
    fi
	return ${result}
}

wait_for_wrapper()
{
	# In order to support SIGINT during timeout: http://unix.stackexchange.com/a/57692
	if [ ${QUIET} -eq 1 ]; then
        ARGS="$debug -q"
    else
        ARGS="$debug"
    fi
    if [ -n "$URL" ]; then
        ARGS="$ARGS -u ${URL} ${USERNAME:+-U ${USERNAME}} ${PASSWORD:+-P ${PASSWORD}}"
    else
        ARGS="-h ${HOST} -p ${PORT}"
    fi

    if [ -n "$(type -t timeout)" ]; then
	    timeout ${BUSYTIMEFLAG} ${TIMEOUT} $0 ${ARGS} -c -t ${TIMEOUT} &
    else
	    gtimeout ${TIMEOUT} $0 ${ARGS} -c -t ${TIMEOUT} &
    fi
        
	PID=$!
	trap "kill -INT -${PID}" INT
	wait ${PID}
	RESULT=$?
	if [[ ${RESULT} -ne 0 ]]; then
        if [ -n "$URL" ]; then
		    echoerr "${cmdname}: timeout occurred after waiting ${TIMEOUT} seconds for ${URL}"
        else
		    echoerr "${cmdname}: timeout occurred after waiting ${TIMEOUT} seconds for ${HOST}:${PORT}"
        fi
	fi
	return ${RESULT}
}

URL=""
USERNAME=""
PASSWORD=""
RETRY_TIME=5
TIMEOUT=15
STRICT=0
CHILD=0
QUIET=0
debug=""
while getopts csSqt:h:p:u:U:P:x OPT; do
	case "${OPT}" in
		c) CHILD=1;;
		s) STRICT=1;;
		S) STRICT=0;;
		q) QUIET=1;;
		t) TIMEOUT=${OPTARG};;
		h) HOST=${OPTARG};;
		p) PORT=${OPTARG};;
        u) URL=${OPTARG};;
        P) PASSWORD=${OPTARG};;
        U) USERNAME=${OPTARG};;
        x) set -x; debug="-x";;
	esac
done

shift `expr ${OPTIND} - 1`
CLI="$@"

if [ -z "$URL" -a \( -z "${HOST}" -o -z "${PORT}" \) ]; then
	echoerr "Error: you need to provide a URL or a host and port to test."
	usage
fi

# check to see if timeout is from busybox?

BUSYBOX="busybox"
if [ "$(type -t timeout)" != builtin ]; then
	ISBUSY=1
	BUSYTIMEFLAG="-t"
else
	ISBUSY=0
	BUSYTIMEFLAG=""
fi

if [ ${CHILD} -gt 0 ]; then
    wait_for
    RESULT=$?
    exit ${RESULT}
else
    if [ ${TIMEOUT} -gt 0 ]; then
        wait_for_wrapper
        RESULT=$?
    else
        wait_for
        RESULT=$?
    fi
fi

if [ -n "${CLI}" ]; then
    if [ ${RESULT} -ne 0 -a ${STRICT} -eq 1 ]; then
        echoerr "${cmdname}: strict mode, refusing to execute subprocess"
        exit ${RESULT}
    fi
    exec ${CLI}
else
    exit ${RESULT}
fi

