/* update bound parameters and variable attributes (start, nominal, min, max) */
#include "artifacts/ct02-exact-two/d00_model.h"
#if defined(__cplusplus)
extern "C" {
#endif

OMC_DISABLE_OPT
int artifacts_ct02_exact_two_d00_updateBoundVariableAttributes(DATA *data, threadData_t *threadData)
{
  /* min ******************************************************** */
  infoStreamPrint(OMC_LOG_INIT, 1, "updating min-values");
  messageClose(OMC_LOG_INIT);
  
  /* max ******************************************************** */
  infoStreamPrint(OMC_LOG_INIT, 1, "updating max-values");
  messageClose(OMC_LOG_INIT);
  
  /* nominal **************************************************** */
  infoStreamPrint(OMC_LOG_INIT, 1, "updating nominal-values");
  messageClose(OMC_LOG_INIT);
  
  /* start ****************************************************** */
  infoStreamPrint(OMC_LOG_INIT, 1, "updating primary start-values");
  messageClose(OMC_LOG_INIT);
  
  return 0;
}

void artifacts_ct02_exact_two_d00_updateBoundParameters_0(DATA *data, threadData_t *threadData);
extern void artifacts_ct02_exact_two_d00_eqFunction_1(DATA *data, threadData_t *threadData);

OMC_DISABLE_OPT
void artifacts_ct02_exact_two_d00_updateBoundParameters_0(DATA *data, threadData_t *threadData)
{
  static void (*const eqFunctions[1])(DATA*, threadData_t*) = {
    artifacts_ct02_exact_two_d00_eqFunction_1
  };
  
  for (int id = 0; id < 1; id++) {
    eqFunctions[id](data, threadData);
  }
}
OMC_DISABLE_OPT
int artifacts_ct02_exact_two_d00_updateBoundParameters(DATA *data, threadData_t *threadData)
{
  artifacts_ct02_exact_two_d00_updateBoundParameters_0(data, threadData);
  return 0;
}

#if defined(__cplusplus)
}
#endif
