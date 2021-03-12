#include "rtklib.h"


int main()
{
    traceopen("rtcm.log");
    tracelevel(5); // debug

    rtcm_t rtcm;
    int rc = init_rtcm(&rtcm);
    if (rc == 0)
    {
        perror("Failed to init rtcm object");
        exit(1);
    }

    size_t bytes_read = 0;
    size_t total_bytes = 0;
    unsigned char buf[1000];

    while ((bytes_read = fread(buf, 1, sizeof(buf), stdin)) > 0)
    {
        total_bytes += bytes_read;
        for (size_t i = 0; i < bytes_read; ++i)
        {
            input_rtcm3(&rtcm, buf[i]);
        }
    }

    free_rtcm(&rtcm);
    traceclose();
    printf("Total bytes parsed: %d\n", (int)total_bytes);
    return 0;
}
