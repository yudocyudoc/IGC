/* Initialization */
#include "artifacts/ct02-exact-two/d00_model.h"
#include "artifacts/ct02-exact-two/d00_11mix.h"
#include "artifacts/ct02-exact-two/d00_12jac.h"
#if defined(__cplusplus)
extern "C" {
#endif

void artifacts_ct02_exact_two_d00_functionInitialEquations_0(DATA *data, threadData_t *threadData);

/*
equation index: 1
type: SIMPLE_ASSIGN
lossRate = 0.0
*/
void artifacts_ct02_exact_two_d00_eqFunction_1(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,1};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[9]] /* lossRate variable */) = 0.0;
  threadData->lastEquationSolved = 1;
}
extern void artifacts_ct02_exact_two_d00_eqFunction_15(DATA *data, threadData_t *threadData);

extern void artifacts_ct02_exact_two_d00_eqFunction_12(DATA *data, threadData_t *threadData);


/*
equation index: 4
type: SIMPLE_ASSIGN
s1 = $START.s1
*/
void artifacts_ct02_exact_two_d00_eqFunction_4(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,4};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[2]] /* s1 STATE(1) */) = ((modelica_real *)((data->modelData->realVarsData[2] /* s1 STATE(1) */).attribute .start.data))[0];
  threadData->lastEquationSolved = 4;
}

/*
equation index: 5
type: SIMPLE_ASSIGN
f1 = min(capacity, max(0.0, s1 / responseTime))
*/
void artifacts_ct02_exact_two_d00_eqFunction_5(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,5};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[7]] /* f1 variable */) = fmin((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[0]] /* capacity PARAM */),fmax(0.0,DIVISION_SIM((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[2]] /* s1 STATE(1) */),(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[4]] /* responseTime PARAM */),"responseTime",equationIndexes)));
  threadData->lastEquationSolved = 5;
}
extern void artifacts_ct02_exact_two_d00_eqFunction_13(DATA *data, threadData_t *threadData);

extern void artifacts_ct02_exact_two_d00_eqFunction_14(DATA *data, threadData_t *threadData);


/*
equation index: 8
type: SIMPLE_ASSIGN
delivered = $START.delivered
*/
void artifacts_ct02_exact_two_d00_eqFunction_8(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,8};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[0]] /* delivered STATE(1,f1) */) = ((modelica_real *)((data->modelData->realVarsData[0] /* delivered STATE(1,f1) */).attribute .start.data))[0];
  threadData->lastEquationSolved = 8;
}

/*
equation index: 9
type: SIMPLE_ASSIGN
lost = $START.lost
*/
void artifacts_ct02_exact_two_d00_eqFunction_9(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,9};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[1]] /* lost STATE(1) */) = ((modelica_real *)((data->modelData->realVarsData[1] /* lost STATE(1) */).attribute .start.data))[0];
  threadData->lastEquationSolved = 9;
}
OMC_DISABLE_OPT
void artifacts_ct02_exact_two_d00_functionInitialEquations_0(DATA *data, threadData_t *threadData)
{
  static void (*const eqFunctions[9])(DATA*, threadData_t*) = {
    artifacts_ct02_exact_two_d00_eqFunction_1,
    artifacts_ct02_exact_two_d00_eqFunction_15,
    artifacts_ct02_exact_two_d00_eqFunction_12,
    artifacts_ct02_exact_two_d00_eqFunction_4,
    artifacts_ct02_exact_two_d00_eqFunction_5,
    artifacts_ct02_exact_two_d00_eqFunction_13,
    artifacts_ct02_exact_two_d00_eqFunction_14,
    artifacts_ct02_exact_two_d00_eqFunction_8,
    artifacts_ct02_exact_two_d00_eqFunction_9
  };
  
  for (int id = 0; id < 9; id++) {
    eqFunctions[id](data, threadData);
  }
}

int artifacts_ct02_exact_two_d00_functionInitialEquations(DATA *data, threadData_t *threadData)
{
  data->simulationInfo->discreteCall = 1;
  artifacts_ct02_exact_two_d00_functionInitialEquations_0(data, threadData);
  data->simulationInfo->discreteCall = 0;
  
  return 0;
}

/* No artifacts_ct02_exact_two_d00_functionInitialEquations_lambda0 function */

int artifacts_ct02_exact_two_d00_functionRemovedInitialEquations(DATA *data, threadData_t *threadData)
{
  const int *equationIndexes = NULL;
  double res = 0.0;

  
  return 0;
}


#if defined(__cplusplus)
}
#endif
