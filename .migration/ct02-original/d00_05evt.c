/* Events: Sample, Zero Crossings, Relations, Discrete Changes */
#include "artifacts/ct02-exact-two/d00_model.h"
#if defined(__cplusplus)
extern "C" {
#endif

/* Initializes the raw time events of the simulation using the now
   calcualted parameters. */
void artifacts_ct02_exact_two_d00_function_initSample(DATA *data, threadData_t *threadData)
{
  long i=0;
}

const char *artifacts_ct02_exact_two_d00_zeroCrossingDescription(int i, int **out_EquationIndexes)
{
  static const char *res[] = {"time < pulseDuration"};
  static const int occurEqs0[] = {1,12};
  static const int *occurEqs[] = {occurEqs0};
  *out_EquationIndexes = (int*) occurEqs[i];
  return res[i];
}

/* forwarded equations */

int artifacts_ct02_exact_two_d00_function_ZeroCrossingsEquations(DATA *data, threadData_t *threadData)
{
  data->simulationInfo->callStatistics.functionZeroCrossingsEquations++;

  
  return 0;
}

int artifacts_ct02_exact_two_d00_function_ZeroCrossings(DATA *data, threadData_t *threadData, double *gout)
{
  const int *equationIndexes = NULL;

  modelica_boolean tmp0;
  modelica_real tmp1;
  modelica_real tmp2;
  modelica_integer current_index = 0;
  modelica_integer start_index;
  
#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_tick(SIM_TIMER_ZC);
#endif
  data->simulationInfo->callStatistics.functionZeroCrossings++;

  start_index = current_index;
  tmp1 = 1.0;
  tmp2 = fabs((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[2]] /* pulseDuration PARAM */));
  tmp0 = LessZC(data->localData[0]->timeValue, (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[2]] /* pulseDuration PARAM */), tmp1, tmp2, data->simulationInfo->storedRelations[0]);
  gout[start_index] = (tmp0) ? 1 : -1;
  current_index++;

#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_accumulate(SIM_TIMER_ZC);
#endif

  return 0;
}

const char *artifacts_ct02_exact_two_d00_relationDescription(int i)
{
  const char *res[] = {"time < pulseDuration"};
  return res[i];
}

int artifacts_ct02_exact_two_d00_function_updateRelations(DATA *data, threadData_t *threadData, int evalforZeroCross)
{
  const int *equationIndexes = NULL;

  modelica_boolean tmp3;
  modelica_real tmp4;
  modelica_real tmp5;
  modelica_integer current_index = 0;
  modelica_integer start_index;
  
  if(evalforZeroCross) {
    start_index = current_index;
    tmp4 = 1.0;
    tmp5 = fabs((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[2]] /* pulseDuration PARAM */));
    tmp3 = LessZC(data->localData[0]->timeValue, (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[2]] /* pulseDuration PARAM */), tmp4, tmp5, data->simulationInfo->storedRelations[0]);
    data->simulationInfo->relations[start_index] = tmp3;
    current_index++;
  } else {
    start_index = current_index;
    data->simulationInfo->relations[start_index] = (data->localData[0]->timeValue < (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[2]] /* pulseDuration PARAM */));
    current_index++;
  }
  
  return 0;
}

#if defined(__cplusplus)
}
#endif
