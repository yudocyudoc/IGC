/* Algebraic */
#include "artifacts/ct02-exact-two/m00_model.h"

#ifdef __cplusplus
extern "C" {
#endif

/* forwarded equations */
extern void artifacts_ct02_exact_two_m00_eqFunction_58(DATA* data, threadData_t *threadData);
extern void artifacts_ct02_exact_two_m00_eqFunction_59(DATA* data, threadData_t *threadData);

static void functionAlg_system0(DATA *data, threadData_t *threadData)
{
  static void (*const eqFunctions[2])(DATA*, threadData_t*) = {
    artifacts_ct02_exact_two_m00_eqFunction_58,
    artifacts_ct02_exact_two_m00_eqFunction_59
  };
  
  for (int id = 0; id < 2; id++) {
    eqFunctions[id](data, threadData);
  }
}
/* for continuous time variables */
int artifacts_ct02_exact_two_m00_functionAlgebraics(DATA *data, threadData_t *threadData)
{

#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_tick(SIM_TIMER_ALGEBRAICS);
#endif
  data->simulationInfo->callStatistics.functionAlgebraics++;

  artifacts_ct02_exact_two_m00_function_savePreSynchronous(data, threadData);
  
  functionAlg_system0(data, threadData);

#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_accumulate(SIM_TIMER_ALGEBRAICS);
#endif

  return 0;
}

#ifdef __cplusplus
}
#endif
