/* Algebraic */
#include "artifacts/ct02-exact-two/d00_model.h"

#ifdef __cplusplus
extern "C" {
#endif

/* for continuous time variables */
int artifacts_ct02_exact_two_d00_functionAlgebraics(DATA *data, threadData_t *threadData)
{

#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_tick(SIM_TIMER_ALGEBRAICS);
#endif
  data->simulationInfo->callStatistics.functionAlgebraics++;

  artifacts_ct02_exact_two_d00_function_savePreSynchronous(data, threadData);
  
  /* no Alg systems */

#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_accumulate(SIM_TIMER_ALGEBRAICS);
#endif

  return 0;
}

#ifdef __cplusplus
}
#endif
