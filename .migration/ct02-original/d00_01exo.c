/* External objects file */
#include "artifacts/ct02-exact-two/d00_model.h"
#if defined(__cplusplus)
extern "C" {
#endif

void artifacts_ct02_exact_two_d00_callExternalObjectDestructors(DATA *data, threadData_t *threadData)
{
  if(data->simulationInfo->extObjs)
  {
    free(data->simulationInfo->extObjs);
    data->simulationInfo->extObjs = 0;
  }
}
#if defined(__cplusplus)
}
#endif
