/* Initialization */
#include "artifacts/ct02-exact-two/m00_model.h"
#include "artifacts/ct02-exact-two/m00_11mix.h"
#include "artifacts/ct02-exact-two/m00_12jac.h"
#if defined(__cplusplus)
extern "C" {
#endif

void artifacts_ct02_exact_two_m00_functionInitialEquations_0(DATA *data, threadData_t *threadData);

/*
equation index: 1
type: SIMPLE_ASSIGN
preparation0.stock.Integrator1.local_reset = false
*/
void artifacts_ct02_exact_two_m00_eqFunction_1(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,1};
  (data->localData[0]->booleanVars[data->simulationInfo->booleanVarsIndex[1]] /* preparation0.stock.Integrator1.local_reset DISCRETE */) = 0 /* false */;
  threadData->lastEquationSolved = 1;
}

/*
equation index: 2
type: SIMPLE_ASSIGN
preparation0.stock.Integrator1.local_set = 0.0
*/
void artifacts_ct02_exact_two_m00_eqFunction_2(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,2};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[17]] /* preparation0.stock.Integrator1.local_set variable */) = 0.0;
  threadData->lastEquationSolved = 2;
}

/*
equation index: 3
type: SIMPLE_ASSIGN
dispatch0.stock.Integrator1.local_reset = false
*/
void artifacts_ct02_exact_two_m00_eqFunction_3(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,3};
  (data->localData[0]->booleanVars[data->simulationInfo->booleanVarsIndex[0]] /* dispatch0.stock.Integrator1.local_reset DISCRETE */) = 0 /* false */;
  threadData->lastEquationSolved = 3;
}

/*
equation index: 4
type: SIMPLE_ASSIGN
dispatch0.stock.Integrator1.local_set = 0.0
*/
void artifacts_ct02_exact_two_m00_eqFunction_4(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,4};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[12]] /* dispatch0.stock.Integrator1.local_set variable */) = 0.0;
  threadData->lastEquationSolved = 4;
}

/*
equation index: 5
type: SIMPLE_ASSIGN
receipt0.deliveries.Integrator1.local_reset = false
*/
void artifacts_ct02_exact_two_m00_eqFunction_5(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,5};
  (data->localData[0]->booleanVars[data->simulationInfo->booleanVarsIndex[2]] /* receipt0.deliveries.Integrator1.local_reset DISCRETE */) = 0 /* false */;
  threadData->lastEquationSolved = 5;
}

/*
equation index: 6
type: SIMPLE_ASSIGN
receipt0.deliveries.Integrator1.local_set = 0.0
*/
void artifacts_ct02_exact_two_m00_eqFunction_6(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,6};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[18]] /* receipt0.deliveries.Integrator1.local_set variable */) = 0.0;
  threadData->lastEquationSolved = 6;
}

/*
equation index: 7
type: SIMPLE_ASSIGN
inTransit = 0.0
*/
void artifacts_ct02_exact_two_m00_eqFunction_7(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,7};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[13]] /* inTransit variable */) = 0.0;
  threadData->lastEquationSolved = 7;
}
extern void artifacts_ct02_exact_two_m00_eqFunction_55(DATA *data, threadData_t *threadData);


/*
equation index: 9
type: SIMPLE_ASSIGN
report0.reportFilter.y = report0.reportFilter.y_start
*/
void artifacts_ct02_exact_two_m00_eqFunction_9(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,9};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[3]] /* report0.reportFilter.y STATE(1) */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[29]] /* report0.reportFilter.y_start PARAM */);
  threadData->lastEquationSolved = 9;
}

/*
equation index: 10
type: SIMPLE_ASSIGN
dispatch0.stock.Integrator1.y = dispatch0.stock.Integrator1.y_start
*/
void artifacts_ct02_exact_two_m00_eqFunction_10(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,10};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[0]] /* dispatch0.stock.Integrator1.y STATE(1) */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[10]] /* dispatch0.stock.Integrator1.y_start PARAM */);
  threadData->lastEquationSolved = 10;
}
extern void artifacts_ct02_exact_two_m00_eqFunction_49(DATA *data, threadData_t *threadData);


/*
equation index: 12
type: SIMPLE_ASSIGN
deliveryRate = homotopy(smooth(0, if dispatch0.release.u > dispatch0.release.Limiter1.uMax then dispatch0.release.Limiter1.uMax else if dispatch0.release.u < dispatch0.release.Limiter1.uMin then dispatch0.release.Limiter1.uMin else dispatch0.release.u), dispatch0.release.u)
*/
void artifacts_ct02_exact_two_m00_eqFunction_12(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,12};
  modelica_boolean tmp0;
  modelica_boolean tmp1;
  modelica_boolean tmp2;
  modelica_real tmp3;
  tmp0 = Greater((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[10]] /* dispatch0.release.u variable */),(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[1]] /* dispatch0.release.Limiter1.uMax PARAM */));
  tmp2 = (modelica_boolean)tmp0;
  if(tmp2)
  {
    tmp3 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[1]] /* dispatch0.release.Limiter1.uMax PARAM */);
  }
  else
  {
    tmp1 = Less((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[10]] /* dispatch0.release.u variable */),(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[2]] /* dispatch0.release.Limiter1.uMin PARAM */));
    tmp3 = (tmp1?(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[2]] /* dispatch0.release.Limiter1.uMin PARAM */):(data->localData[0]->realVars[data->simulationInfo->realVarsIndex[10]] /* dispatch0.release.u variable */));
  }
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[8]] /* deliveryRate variable */) = homotopy(tmp3, (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[10]] /* dispatch0.release.u variable */));
  threadData->lastEquationSolved = 12;
}
extern void artifacts_ct02_exact_two_m00_eqFunction_53(DATA *data, threadData_t *threadData);

extern void artifacts_ct02_exact_two_m00_eqFunction_54(DATA *data, threadData_t *threadData);


/*
equation index: 15
type: SIMPLE_ASSIGN
preparation0.stock.Integrator1.y = preparation0.stock.Integrator1.y_start
*/
void artifacts_ct02_exact_two_m00_eqFunction_15(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,15};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[1]] /* preparation0.stock.Integrator1.y STATE(1) */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[22]] /* preparation0.stock.Integrator1.y_start PARAM */);
  threadData->lastEquationSolved = 15;
}
extern void artifacts_ct02_exact_two_m00_eqFunction_47(DATA *data, threadData_t *threadData);


/*
equation index: 17
type: SIMPLE_ASSIGN
dispatch0.inflow.rate = homotopy(smooth(0, if preparation0.release.u > preparation0.release.Limiter1.uMax then preparation0.release.Limiter1.uMax else if preparation0.release.u < preparation0.release.Limiter1.uMin then preparation0.release.Limiter1.uMin else preparation0.release.u), preparation0.release.u)
*/
void artifacts_ct02_exact_two_m00_eqFunction_17(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,17};
  modelica_boolean tmp4;
  modelica_boolean tmp5;
  modelica_boolean tmp6;
  modelica_real tmp7;
  tmp4 = Greater((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[15]] /* preparation0.release.u variable */),(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[13]] /* preparation0.release.Limiter1.uMax PARAM */));
  tmp6 = (modelica_boolean)tmp4;
  if(tmp6)
  {
    tmp7 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[13]] /* preparation0.release.Limiter1.uMax PARAM */);
  }
  else
  {
    tmp5 = Less((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[15]] /* preparation0.release.u variable */),(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[14]] /* preparation0.release.Limiter1.uMin PARAM */));
    tmp7 = (tmp5?(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[14]] /* preparation0.release.Limiter1.uMin PARAM */):(data->localData[0]->realVars[data->simulationInfo->realVarsIndex[15]] /* preparation0.release.u variable */));
  }
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[9]] /* dispatch0.inflow.rate variable */) = homotopy(tmp7, (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[15]] /* preparation0.release.u variable */));
  threadData->lastEquationSolved = 17;
}
extern void artifacts_ct02_exact_two_m00_eqFunction_56(DATA *data, threadData_t *threadData);

extern void artifacts_ct02_exact_two_m00_eqFunction_57(DATA *data, threadData_t *threadData);

extern void artifacts_ct02_exact_two_m00_eqFunction_51(DATA *data, threadData_t *threadData);

extern void artifacts_ct02_exact_two_m00_eqFunction_52(DATA *data, threadData_t *threadData);


/*
equation index: 22
type: SIMPLE_ASSIGN
receipt0.deliveries.Integrator1.y = receipt0.deliveries.Integrator1.y_start
*/
void artifacts_ct02_exact_two_m00_eqFunction_22(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,22};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[2]] /* receipt0.deliveries.Integrator1.y STATE(1) */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[25]] /* receipt0.deliveries.Integrator1.y_start PARAM */);
  threadData->lastEquationSolved = 22;
}

/*
equation index: 24
type: ALGORITHM

  assert(preparation0.release.Limiter1.uMax >= preparation0.release.Limiter1.uMin, "Limiter: Limits must be consistent. However, uMax (=" + String(preparation0.release.Limiter1.uMax, 6, 0, true) + ") < uMin (=" + String(preparation0.release.Limiter1.uMin, 6, 0, true) + ")");
*/
void artifacts_ct02_exact_two_m00_eqFunction_24(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,24};
  modelica_boolean tmp8;
  static const MMC_DEFSTRINGLIT(tmp9,52,"Limiter: Limits must be consistent. However, uMax (=");
  modelica_string tmp10;
  modelica_metatype tmpMeta11;
  static const MMC_DEFSTRINGLIT(tmp12,11,") < uMin (=");
  modelica_metatype tmpMeta13;
  modelica_string tmp14;
  modelica_metatype tmpMeta15;
  modelica_metatype tmpMeta16;
  static int tmp17 = 0;
  {
    tmp8 = GreaterEq((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[13]] /* preparation0.release.Limiter1.uMax PARAM */),(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[14]] /* preparation0.release.Limiter1.uMin PARAM */));
    if(!tmp8)
    {
      tmp10 = modelica_real_to_modelica_string((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[13]] /* preparation0.release.Limiter1.uMax PARAM */), ((modelica_integer) 6), ((modelica_integer) 0), 1 /* true */);
      tmpMeta11 = stringAppend(MMC_REFSTRINGLIT(tmp9),tmp10);
      tmpMeta13 = stringAppend(tmpMeta11,MMC_REFSTRINGLIT(tmp12));
      tmp14 = modelica_real_to_modelica_string((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[14]] /* preparation0.release.Limiter1.uMin PARAM */), ((modelica_integer) 6), ((modelica_integer) 0), 1 /* true */);
      tmpMeta15 = stringAppend(tmpMeta13,tmp14);
      tmpMeta16 = stringAppend(tmpMeta15,(modelica_string) mmc_strings_len1[41]);
      {
        const char* assert_cond = "(preparation0.release.Limiter1.uMax >= preparation0.release.Limiter1.uMin)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/thirdparty/msl/Modelica/Blocks/Nonlinear.mo",19,9,20,65,1};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta16));
          data->simulationInfo->needToReThrow = 1;
        } else {
          FILE_INFO info = {"/thirdparty/msl/Modelica/Blocks/Nonlinear.mo",19,9,20,65,1};
          omc_assert_withEquationIndexes(threadData, info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta16));
        }
      }
    }
  }
  threadData->lastEquationSolved = 24;
}

/*
equation index: 23
type: ALGORITHM

  assert(dispatch0.release.Limiter1.uMax >= dispatch0.release.Limiter1.uMin, "Limiter: Limits must be consistent. However, uMax (=" + String(dispatch0.release.Limiter1.uMax, 6, 0, true) + ") < uMin (=" + String(dispatch0.release.Limiter1.uMin, 6, 0, true) + ")");
*/
void artifacts_ct02_exact_two_m00_eqFunction_23(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,23};
  modelica_boolean tmp18;
  static const MMC_DEFSTRINGLIT(tmp19,52,"Limiter: Limits must be consistent. However, uMax (=");
  modelica_string tmp20;
  modelica_metatype tmpMeta21;
  static const MMC_DEFSTRINGLIT(tmp22,11,") < uMin (=");
  modelica_metatype tmpMeta23;
  modelica_string tmp24;
  modelica_metatype tmpMeta25;
  modelica_metatype tmpMeta26;
  static int tmp27 = 0;
  {
    tmp18 = GreaterEq((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[1]] /* dispatch0.release.Limiter1.uMax PARAM */),(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[2]] /* dispatch0.release.Limiter1.uMin PARAM */));
    if(!tmp18)
    {
      tmp20 = modelica_real_to_modelica_string((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[1]] /* dispatch0.release.Limiter1.uMax PARAM */), ((modelica_integer) 6), ((modelica_integer) 0), 1 /* true */);
      tmpMeta21 = stringAppend(MMC_REFSTRINGLIT(tmp19),tmp20);
      tmpMeta23 = stringAppend(tmpMeta21,MMC_REFSTRINGLIT(tmp22));
      tmp24 = modelica_real_to_modelica_string((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[2]] /* dispatch0.release.Limiter1.uMin PARAM */), ((modelica_integer) 6), ((modelica_integer) 0), 1 /* true */);
      tmpMeta25 = stringAppend(tmpMeta23,tmp24);
      tmpMeta26 = stringAppend(tmpMeta25,(modelica_string) mmc_strings_len1[41]);
      {
        const char* assert_cond = "(dispatch0.release.Limiter1.uMax >= dispatch0.release.Limiter1.uMin)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/thirdparty/msl/Modelica/Blocks/Nonlinear.mo",19,9,20,65,1};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta26));
          data->simulationInfo->needToReThrow = 1;
        } else {
          FILE_INFO info = {"/thirdparty/msl/Modelica/Blocks/Nonlinear.mo",19,9,20,65,1};
          omc_assert_withEquationIndexes(threadData, info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta26));
        }
      }
    }
  }
  threadData->lastEquationSolved = 23;
}
OMC_DISABLE_OPT
void artifacts_ct02_exact_two_m00_functionInitialEquations_0(DATA *data, threadData_t *threadData)
{
  static void (*const eqFunctions[24])(DATA*, threadData_t*) = {
    artifacts_ct02_exact_two_m00_eqFunction_1,
    artifacts_ct02_exact_two_m00_eqFunction_2,
    artifacts_ct02_exact_two_m00_eqFunction_3,
    artifacts_ct02_exact_two_m00_eqFunction_4,
    artifacts_ct02_exact_two_m00_eqFunction_5,
    artifacts_ct02_exact_two_m00_eqFunction_6,
    artifacts_ct02_exact_two_m00_eqFunction_7,
    artifacts_ct02_exact_two_m00_eqFunction_55,
    artifacts_ct02_exact_two_m00_eqFunction_9,
    artifacts_ct02_exact_two_m00_eqFunction_10,
    artifacts_ct02_exact_two_m00_eqFunction_49,
    artifacts_ct02_exact_two_m00_eqFunction_12,
    artifacts_ct02_exact_two_m00_eqFunction_53,
    artifacts_ct02_exact_two_m00_eqFunction_54,
    artifacts_ct02_exact_two_m00_eqFunction_15,
    artifacts_ct02_exact_two_m00_eqFunction_47,
    artifacts_ct02_exact_two_m00_eqFunction_17,
    artifacts_ct02_exact_two_m00_eqFunction_56,
    artifacts_ct02_exact_two_m00_eqFunction_57,
    artifacts_ct02_exact_two_m00_eqFunction_51,
    artifacts_ct02_exact_two_m00_eqFunction_52,
    artifacts_ct02_exact_two_m00_eqFunction_22,
    artifacts_ct02_exact_two_m00_eqFunction_24,
    artifacts_ct02_exact_two_m00_eqFunction_23
  };
  
  for (int id = 0; id < 24; id++) {
    eqFunctions[id](data, threadData);
  }
}

int artifacts_ct02_exact_two_m00_functionInitialEquations(DATA *data, threadData_t *threadData)
{
  data->simulationInfo->discreteCall = 1;
  artifacts_ct02_exact_two_m00_functionInitialEquations_0(data, threadData);
  data->simulationInfo->discreteCall = 0;
  
  return 0;
}
extern void artifacts_ct02_exact_two_m00_eqFunction_1(DATA *data, threadData_t *threadData);

extern void artifacts_ct02_exact_two_m00_eqFunction_2(DATA *data, threadData_t *threadData);

extern void artifacts_ct02_exact_two_m00_eqFunction_3(DATA *data, threadData_t *threadData);

extern void artifacts_ct02_exact_two_m00_eqFunction_4(DATA *data, threadData_t *threadData);

extern void artifacts_ct02_exact_two_m00_eqFunction_5(DATA *data, threadData_t *threadData);

extern void artifacts_ct02_exact_two_m00_eqFunction_6(DATA *data, threadData_t *threadData);

extern void artifacts_ct02_exact_two_m00_eqFunction_7(DATA *data, threadData_t *threadData);

extern void artifacts_ct02_exact_two_m00_eqFunction_55(DATA *data, threadData_t *threadData);

extern void artifacts_ct02_exact_two_m00_eqFunction_9(DATA *data, threadData_t *threadData);

extern void artifacts_ct02_exact_two_m00_eqFunction_10(DATA *data, threadData_t *threadData);

extern void artifacts_ct02_exact_two_m00_eqFunction_49(DATA *data, threadData_t *threadData);


/*
equation index: 36
type: SIMPLE_ASSIGN
deliveryRate = dispatch0.release.u
*/
void artifacts_ct02_exact_two_m00_eqFunction_36(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,36};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[8]] /* deliveryRate variable */) = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[10]] /* dispatch0.release.u variable */);
  threadData->lastEquationSolved = 36;
}
extern void artifacts_ct02_exact_two_m00_eqFunction_53(DATA *data, threadData_t *threadData);

extern void artifacts_ct02_exact_two_m00_eqFunction_54(DATA *data, threadData_t *threadData);

extern void artifacts_ct02_exact_two_m00_eqFunction_15(DATA *data, threadData_t *threadData);

extern void artifacts_ct02_exact_two_m00_eqFunction_47(DATA *data, threadData_t *threadData);


/*
equation index: 41
type: SIMPLE_ASSIGN
dispatch0.inflow.rate = preparation0.release.u
*/
void artifacts_ct02_exact_two_m00_eqFunction_41(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,41};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[9]] /* dispatch0.inflow.rate variable */) = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[15]] /* preparation0.release.u variable */);
  threadData->lastEquationSolved = 41;
}
extern void artifacts_ct02_exact_two_m00_eqFunction_56(DATA *data, threadData_t *threadData);

extern void artifacts_ct02_exact_two_m00_eqFunction_57(DATA *data, threadData_t *threadData);

extern void artifacts_ct02_exact_two_m00_eqFunction_51(DATA *data, threadData_t *threadData);

extern void artifacts_ct02_exact_two_m00_eqFunction_52(DATA *data, threadData_t *threadData);

extern void artifacts_ct02_exact_two_m00_eqFunction_22(DATA *data, threadData_t *threadData);

int artifacts_ct02_exact_two_m00_functionInitialEquations_lambda0(DATA *data, threadData_t *threadData)
{
  data->simulationInfo->discreteCall = 1;
  static void (*const eqFunctions[22])(DATA*, threadData_t*) = {
    artifacts_ct02_exact_two_m00_eqFunction_1,
    artifacts_ct02_exact_two_m00_eqFunction_2,
    artifacts_ct02_exact_two_m00_eqFunction_3,
    artifacts_ct02_exact_two_m00_eqFunction_4,
    artifacts_ct02_exact_two_m00_eqFunction_5,
    artifacts_ct02_exact_two_m00_eqFunction_6,
    artifacts_ct02_exact_two_m00_eqFunction_7,
    artifacts_ct02_exact_two_m00_eqFunction_55,
    artifacts_ct02_exact_two_m00_eqFunction_9,
    artifacts_ct02_exact_two_m00_eqFunction_10,
    artifacts_ct02_exact_two_m00_eqFunction_49,
    artifacts_ct02_exact_two_m00_eqFunction_36,
    artifacts_ct02_exact_two_m00_eqFunction_53,
    artifacts_ct02_exact_two_m00_eqFunction_54,
    artifacts_ct02_exact_two_m00_eqFunction_15,
    artifacts_ct02_exact_two_m00_eqFunction_47,
    artifacts_ct02_exact_two_m00_eqFunction_41,
    artifacts_ct02_exact_two_m00_eqFunction_56,
    artifacts_ct02_exact_two_m00_eqFunction_57,
    artifacts_ct02_exact_two_m00_eqFunction_51,
    artifacts_ct02_exact_two_m00_eqFunction_52,
    artifacts_ct02_exact_two_m00_eqFunction_22
  };
  
  for (int id = 0; id < 22; id++) {
    eqFunctions[id](data, threadData);
  }
  data->simulationInfo->discreteCall = 0;
  
  return 0;
}
int artifacts_ct02_exact_two_m00_functionRemovedInitialEquations(DATA *data, threadData_t *threadData)
{
  const int *equationIndexes = NULL;
  double res = 0.0;

  
  return 0;
}


#if defined(__cplusplus)
}
#endif
