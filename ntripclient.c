#include <getopt.h>
#include <fcntl.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <curl/curl.h>

#define VERSION         "1.0.0"
#define NTRIP_VER_STR   "Ntrip-Version: Ntrip/2.0"
#define USER_AGENT_STR  "User-Agent: NTRIP NtripClientMatternet/0.1"
#define PROTO_HTTP      "http://"
#define PROTO_HTTPS     "https://"
#define MAX_DATA_SIZE   1000

#ifdef DEBUG
  #define IS_VERBOSE 1
#else
  #define IS_VERBOSE 0
#endif


typedef struct
{
    const char *server;
    const char *mountpoint;
    const char *port;
    const char *user;
    const char *password;
    const char *nmea;
    bool use_tls;
} Args;


static void help()
{
    fprintf(stderr, "Version " VERSION "\n"
            "Usage: ntripclient [OPTIONS] ...\n"
            " -s  the server name or address\n"
            " -m  the requested data set or sourcetable filtering criteria\n"
            " -r  the server port number (default 2101)\n"
            " -u  the user name\n"
            " -p  the login password\n"
            " -n  NMEA string for sending to server\n"
            " -T  Use TLS (HTTPS)\n");
    exit(1);
}

static int parse_args(int argc, char **argv, Args *args)
{
    int opt = 0;
    memset(args, 0, sizeof(Args));

    do
    {
        switch((opt = getopt(argc, argv, "s:m:r:u:p:n:T")))
        {
        case 's': args->server = optarg;       break;
        case 'm': args->mountpoint = optarg;   break;
        case 'r': args->port = optarg;         break;
        case 'u': args->user = optarg;         break;
        case 'p': args->password = optarg;     break;
        case 'n': args->nmea = optarg;         break;
        case 'T': args->use_tls = true;        break;
        case  -1: /* done */                   break;
        default : help();                      break;
        }
    } while (opt != -1);

    // Make sure port is a number
    if (atoi(args->port) == 0)
        help();

    return 0;
}

static int init()
{
    setbuf(stdout, 0);
    setbuf(stdin, 0);
    setbuf(stderr, 0);

    // setup reading from stdin to non-blocking
    int flags = fcntl(0, F_GETFL);
    int ret = fcntl(0, F_SETFL, flags | O_NONBLOCK);
    return ret;
}

static bool valid_header(char *buffer, char *expect, int peek_len)
{
    if (strncmp(buffer, expect, peek_len) == 0)
    {
        return strncmp(buffer, expect, strlen(expect)) == 0;
    }
    return true;  // ignore
}

static size_t cb_header(char *buffer, size_t size, size_t count, void *userdata)
{
    (void)userdata;  // not used

    if (valid_header(buffer, "HTTP/1.1 200 OK\r\n",          5) &&
        valid_header(buffer, "Content-Type: gnss/data\r\n",  13) &&
        valid_header(buffer, "Ntrip-Version: Ntrip/2.0\r\n", 14))
    {
        return size * count;
    }
    return 0; // report error
}

static size_t cb_body_data(void *ptr, size_t size, size_t count, void *userdata)
{
    CURL *curl = (CURL*)userdata;
    size_t len = size * count;

    // Write data to standard out
    fwrite(ptr, len, 1, stdout);

    // TODO: send GGA data at 1Hz
    //size_t bytes_sent;
    //curl_easy_send(curl, "testing\r\n", 9, &bytes_sent);
    return len;
}

static int run(const Args *args)
{
    int ret = -1;
    CURL *curl;

    curl_global_init(CURL_GLOBAL_DEFAULT);
    curl = curl_easy_init();

    if (curl)
    {
        CURLcode res;

        // create url string
        char url[1024];
        const char *proto = args->use_tls ? PROTO_HTTPS : PROTO_HTTP;
        snprintf(url, sizeof(url), "%s%s/%s", proto, args->server, args->mountpoint);
        url[sizeof(url)-1] = 0;

        // Set CURL options
        curl_easy_setopt(curl, CURLOPT_URL, url);
        curl_easy_setopt(curl, CURLOPT_PORT, atoi(args->port));
        curl_easy_setopt(curl, CURLOPT_USERNAME, args->user);
        curl_easy_setopt(curl, CURLOPT_PASSWORD, args->password);
        curl_easy_setopt(curl, CURLOPT_HTTPGET, 1L);
        curl_easy_setopt(curl, CURLOPT_HTTP_VERSION, CURL_HTTP_VERSION_1_1);
        curl_easy_setopt(curl, CURLOPT_HEADERFUNCTION, cb_header);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, cb_body_data);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void*)curl);
        curl_easy_setopt(curl, CURLOPT_VERBOSE, IS_VERBOSE);

        if (args->use_tls)
        {
            curl_easy_setopt(curl, CURLOPT_SSLVERSION, CURL_SSLVERSION_TLSv1_3);
        }

        // Set NTRIP header fields
        struct curl_slist *headers = NULL;
        headers = curl_slist_append(headers, NTRIP_VER_STR);
        headers = curl_slist_append(headers, USER_AGENT_STR);

        if (args->nmea != NULL)
        {
            char nmea[500];
            snprintf(nmea, sizeof(nmea), "Ntrip-GGA: %s", args->nmea);
            nmea[sizeof(nmea)-1] = 0;
            headers = curl_slist_append(headers, nmea);
        }

        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);

        // Run CURL
        res = curl_easy_perform(curl);
        if (res != CURLE_OK)
        {
            fprintf(stderr, "failed: %s\n", curl_easy_strerror(res));
        }
        else
        {
            ret = 0;
        }

        curl_easy_cleanup(curl);
    }

    curl_global_cleanup();
    return ret;
}

int main(int argc, char **argv)
{
    Args args;
    int ret = parse_args(argc, argv, &args);

    if (ret == 0)
        ret = init();

    if (ret == 0)
        ret = run(&args);

    return ret;
}
