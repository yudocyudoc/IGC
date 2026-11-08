/* Main Simulation File */

#if defined(__cplusplus)
extern "C" {
#endif

#include "artifacts/ct02-exact-two/m00_model.h"
#include "simulation/solver/events.h"
#include "util/real_array.h"

/* FIXME these defines are ugly and hard to read, why not use direct function pointers instead? */
#define prefixedName_performSimulation artifacts_ct02_exact_two_m00_performSimulation
#define prefixedName_updateContinuousSystem artifacts_ct02_exact_two_m00_updateContinuousSystem
#include <simulation/solver/perform_simulation.c.inc>

#define prefixedName_performQSSSimulation artifacts_ct02_exact_two_m00_performQSSSimulation
#include <simulation/solver/perform_qss_simulation.c.inc>


/* dummy VARINFO and FILEINFO */
const VAR_INFO dummyVAR_INFO = omc_dummyVarInfo;

int artifacts_ct02_exact_two_m00_input_function(DATA *data, threadData_t *threadData)
{
  
  return 0;
}

int artifacts_ct02_exact_two_m00_input_function_init(DATA *data, threadData_t *threadData)
{
  
  return 0;
}

int artifacts_ct02_exact_two_m00_input_function_updateStartValues(DATA *data, threadData_t *threadData)
{
  
  return 0;
}

int artifacts_ct02_exact_two_m00_inputNames(DATA *data, char ** names){
  
  return 0;
}

int artifacts_ct02_exact_two_m00_data_function(DATA *data, threadData_t *threadData)
{
  return 0;
}

int artifacts_ct02_exact_two_m00_dataReconciliationInputNames(DATA *data, char ** names){
  
  return 0;
}

int artifacts_ct02_exact_two_m00_dataReconciliationUnmeasuredVariables(DATA *data, char ** names)
{
  
  return 0;
}

int artifacts_ct02_exact_two_m00_output_function(DATA *data, threadData_t *threadData)
{
  
  return 0;
}

int artifacts_ct02_exact_two_m00_setc_function(DATA *data, threadData_t *threadData)
{
  
  return 0;
}

int artifacts_ct02_exact_two_m00_setb_function(DATA *data, threadData_t *threadData)
{
  
  return 0;
}


/*
equation index: 47
type: SIMPLE_ASSIGN
preparation0.release.u = preparation0.response.k * preparation0.stock.Integrator1.y
*/
void artifacts_ct02_exact_two_m00_eqFunction_47(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,47};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[15]] /* preparation0.release.u variable */) = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[17]] /* preparation0.response.k PARAM */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[1]] /* preparation0.stock.Integrator1.y STATE(1) */));
  threadData->lastEquationSolved = 47;
}

/*
equation index: 48
type: SIMPLE_ASSIGN
dispatch0.inflow.rate = smooth(0, if preparation0.release.u > preparation0.release.Limiter1.uMax then preparation0.release.Limiter1.uMax else if preparation0.release.u < preparation0.release.Limiter1.uMin then preparation0.release.Limiter1.uMin else preparation0.release.u)
*/
void artifacts_ct02_exact_two_m00_eqFunction_48(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,48};
  modelica_boolean tmp0;
  modelica_boolean tmp1;
  modelica_boolean tmp2;
  modelica_real tmp3;
  tmp0 = Greater((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[15]] /* preparation0.release.u variable */),(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[13]] /* preparation0.release.Limiter1.uMax PARAM */));
  tmp2 = (modelica_boolean)tmp0;
  if(tmp2)
  {
    tmp3 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[13]] /* preparation0.release.Limiter1.uMax PARAM */);
  }
  else
  {
    tmp1 = Less((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[15]] /* preparation0.release.u variable */),(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[14]] /* preparation0.release.Limiter1.uMin PARAM */));
    tmp3 = (tmp1?(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[14]] /* preparation0.release.Limiter1.uMin PARAM */):(data->localData[0]->realVars[data->simulationInfo->realVarsIndex[15]] /* preparation0.release.u variable */));
  }
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[9]] /* dispatch0.inflow.rate variable */) = tmp3;
  threadData->lastEquationSolved = 48;
}

/*
equation index: 49
type: SIMPLE_ASSIGN
dispatch0.release.u = dispatch0.response.k * dispatch0.stock.Integrator1.y
*/
void artifacts_ct02_exact_two_m00_eqFunction_49(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,49};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[10]] /* dispatch0.release.u variable */) = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[5]] /* dispatch0.response.k PARAM */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[0]] /* dispatch0.stock.Integrator1.y STATE(1) */));
  threadData->lastEquationSolved = 49;
}

/*
equation index: 50
type: SIMPLE_ASSIGN
deliveryRate = smooth(0, if dispatch0.release.u > dispatch0.release.Limiter1.uMax then dispatch0.release.Limiter1.uMax else if dispatch0.release.u < dispatch0.release.Limiter1.uMin then dispatch0.release.Limiter1.uMin else dispatch0.release.u)
*/
void artifacts_ct02_exact_two_m00_eqFunction_50(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,50};
  modelica_boolean tmp4;
  modelica_boolean tmp5;
  modelica_boolean tmp6;
  modelica_real tmp7;
  tmp4 = Greater((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[10]] /* dispatch0.release.u variable */),(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[1]] /* dispatch0.release.Limiter1.uMax PARAM */));
  tmp6 = (modelica_boolean)tmp4;
  if(tmp6)
  {
    tmp7 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[1]] /* dispatch0.release.Limiter1.uMax PARAM */);
  }
  else
  {
    tmp5 = Less((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[10]] /* dispatch0.release.u variable */),(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[2]] /* dispatch0.release.Limiter1.uMin PARAM */));
    tmp7 = (tmp5?(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[2]] /* dispatch0.release.Limiter1.uMin PARAM */):(data->localData[0]->realVars[data->simulationInfo->realVarsIndex[10]] /* dispatch0.release.u variable */));
  }
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[8]] /* deliveryRate variable */) = tmp7;
  threadData->lastEquationSolved = 50;
}

/*
equation index: 51
type: SIMPLE_ASSIGN
dispatch0.stock.Add1.y = dispatch0.stock.Add1.k1 * dispatch0.inflow.rate + dispatch0.stock.Add1.k2 * deliveryRate
*/
void artifacts_ct02_exact_two_m00_eqFunction_51(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,51};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[11]] /* dispatch0.stock.Add1.y variable */) = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[7]] /* dispatch0.stock.Add1.k1 PARAM */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[9]] /* dispatch0.inflow.rate variable */)) + ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[8]] /* dispatch0.stock.Add1.k2 PARAM */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[8]] /* deliveryRate variable */));
  threadData->lastEquationSolved = 51;
}

/*
equation index: 52
type: SIMPLE_ASSIGN
$DER.dispatch0.stock.Integrator1.y = dispatch0.stock.Integrator1.k * dispatch0.stock.Add1.y
*/
void artifacts_ct02_exact_two_m00_eqFunction_52(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,52};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[4]] /* der(dispatch0.stock.Integrator1.y) STATE_DER */) = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[9]] /* dispatch0.stock.Integrator1.k PARAM */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[11]] /* dispatch0.stock.Add1.y variable */));
  threadData->lastEquationSolved = 52;
}

/*
equation index: 53
type: SIMPLE_ASSIGN
$DER.receipt0.deliveries.Integrator1.y = receipt0.deliveries.Integrator1.k * deliveryRate
*/
void artifacts_ct02_exact_two_m00_eqFunction_53(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,53};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[6]] /* der(receipt0.deliveries.Integrator1.y) STATE_DER */) = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[24]] /* receipt0.deliveries.Integrator1.k PARAM */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[8]] /* deliveryRate variable */));
  threadData->lastEquationSolved = 53;
}

/*
equation index: 54
type: SIMPLE_ASSIGN
$DER.report0.reportFilter.y = (report0.reportFilter.k * deliveryRate - report0.reportFilter.y) / report0.reportFilter.T
*/
void artifacts_ct02_exact_two_m00_eqFunction_54(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,54};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[7]] /* der(report0.reportFilter.y) STATE_DER */) = DIVISION_SIM(((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[28]] /* report0.reportFilter.k PARAM */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[8]] /* deliveryRate variable */)) - (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[3]] /* report0.reportFilter.y STATE(1) */),(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[27]] /* report0.reportFilter.T PARAM */),"report0.reportFilter.T",equationIndexes);
  threadData->lastEquationSolved = 54;
}

/*
equation index: 55
type: SIMPLE_ASSIGN
preparation0.inflow.rate = if time < 2.0 then 1.7 else 0.0
*/
void artifacts_ct02_exact_two_m00_eqFunction_55(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,55};
  modelica_boolean tmp8;
  modelica_real tmp9;
  modelica_real tmp10;
  tmp9 = 1.0;
  tmp10 = 2.0;
  relationhysteresis(data, &tmp8, data->localData[0]->timeValue, 2.0, tmp9, tmp10, 0, Less, LessZC);
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[14]] /* preparation0.inflow.rate variable */) = (tmp8?1.7:0.0);
  threadData->lastEquationSolved = 55;
}

/*
equation index: 56
type: SIMPLE_ASSIGN
preparation0.stock.Add1.y = preparation0.stock.Add1.k1 * preparation0.inflow.rate + preparation0.stock.Add1.k2 * dispatch0.inflow.rate
*/
void artifacts_ct02_exact_two_m00_eqFunction_56(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,56};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[16]] /* preparation0.stock.Add1.y variable */) = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[19]] /* preparation0.stock.Add1.k1 PARAM */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[14]] /* preparation0.inflow.rate variable */)) + ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[20]] /* preparation0.stock.Add1.k2 PARAM */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[9]] /* dispatch0.inflow.rate variable */));
  threadData->lastEquationSolved = 56;
}

/*
equation index: 57
type: SIMPLE_ASSIGN
$DER.preparation0.stock.Integrator1.y = preparation0.stock.Integrator1.k * preparation0.stock.Add1.y
*/
void artifacts_ct02_exact_two_m00_eqFunction_57(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,57};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[5]] /* der(preparation0.stock.Integrator1.y) STATE_DER */) = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[21]] /* preparation0.stock.Integrator1.k PARAM */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[16]] /* preparation0.stock.Add1.y variable */));
  threadData->lastEquationSolved = 57;
}

/*
equation index: 59
type: ALGORITHM

  assert(preparation0.release.Limiter1.uMax >= preparation0.release.Limiter1.uMin, "Limiter: Limits must be consistent. However, uMax (=" + String(preparation0.release.Limiter1.uMax, 6, 0, true) + ") < uMin (=" + String(preparation0.release.Limiter1.uMin, 6, 0, true) + ")");
*/
void artifacts_ct02_exact_two_m00_eqFunction_59(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,59};
  modelica_boolean tmp11;
  static const MMC_DEFSTRINGLIT(tmp12,52,"Limiter: Limits must be consistent. However, uMax (=");
  modelica_string tmp13;
  modelica_metatype tmpMeta14;
  static const MMC_DEFSTRINGLIT(tmp15,11,") < uMin (=");
  modelica_metatype tmpMeta16;
  modelica_string tmp17;
  modelica_metatype tmpMeta18;
  modelica_metatype tmpMeta19;
  static int tmp20 = 0;
  {
    tmp11 = GreaterEq((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[13]] /* preparation0.release.Limiter1.uMax PARAM */),(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[14]] /* preparation0.release.Limiter1.uMin PARAM */));
    if(!tmp11)
    {
      tmp13 = modelica_real_to_modelica_string((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[13]] /* preparation0.release.Limiter1.uMax PARAM */), ((modelica_integer) 6), ((modelica_integer) 0), 1 /* true */);
      tmpMeta14 = stringAppend(MMC_REFSTRINGLIT(tmp12),tmp13);
      tmpMeta16 = stringAppend(tmpMeta14,MMC_REFSTRINGLIT(tmp15));
      tmp17 = modelica_real_to_modelica_string((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[14]] /* preparation0.release.Limiter1.uMin PARAM */), ((modelica_integer) 6), ((modelica_integer) 0), 1 /* true */);
      tmpMeta18 = stringAppend(tmpMeta16,tmp17);
      tmpMeta19 = stringAppend(tmpMeta18,(modelica_string) mmc_strings_len1[41]);
      {
        const char* assert_cond = "(preparation0.release.Limiter1.uMax >= preparation0.release.Limiter1.uMin)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/thirdparty/msl/Modelica/Blocks/Nonlinear.mo",19,9,20,65,1};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta19));
          data->simulationInfo->needToReThrow = 1;
        } else {
          FILE_INFO info = {"/thirdparty/msl/Modelica/Blocks/Nonlinear.mo",19,9,20,65,1};
          omc_assert_withEquationIndexes(threadData, info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta19));
        }
      }
    }
  }
  threadData->lastEquationSolved = 59;
}

/*
equation index: 58
type: ALGORITHM

  assert(dispatch0.release.Limiter1.uMax >= dispatch0.release.Limiter1.uMin, "Limiter: Limits must be consistent. However, uMax (=" + String(dispatch0.release.Limiter1.uMax, 6, 0, true) + ") < uMin (=" + String(dispatch0.release.Limiter1.uMin, 6, 0, true) + ")");
*/
void artifacts_ct02_exact_two_m00_eqFunction_58(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,58};
  modelica_boolean tmp21;
  static const MMC_DEFSTRINGLIT(tmp22,52,"Limiter: Limits must be consistent. However, uMax (=");
  modelica_string tmp23;
  modelica_metatype tmpMeta24;
  static const MMC_DEFSTRINGLIT(tmp25,11,") < uMin (=");
  modelica_metatype tmpMeta26;
  modelica_string tmp27;
  modelica_metatype tmpMeta28;
  modelica_metatype tmpMeta29;
  static int tmp30 = 0;
  {
    tmp21 = GreaterEq((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[1]] /* dispatch0.release.Limiter1.uMax PARAM */),(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[2]] /* dispatch0.release.Limiter1.uMin PARAM */));
    if(!tmp21)
    {
      tmp23 = modelica_real_to_modelica_string((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[1]] /* dispatch0.release.Limiter1.uMax PARAM */), ((modelica_integer) 6), ((modelica_integer) 0), 1 /* true */);
      tmpMeta24 = stringAppend(MMC_REFSTRINGLIT(tmp22),tmp23);
      tmpMeta26 = stringAppend(tmpMeta24,MMC_REFSTRINGLIT(tmp25));
      tmp27 = modelica_real_to_modelica_string((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[2]] /* dispatch0.release.Limiter1.uMin PARAM */), ((modelica_integer) 6), ((modelica_integer) 0), 1 /* true */);
      tmpMeta28 = stringAppend(tmpMeta26,tmp27);
      tmpMeta29 = stringAppend(tmpMeta28,(modelica_string) mmc_strings_len1[41]);
      {
        const char* assert_cond = "(dispatch0.release.Limiter1.uMax >= dispatch0.release.Limiter1.uMin)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/thirdparty/msl/Modelica/Blocks/Nonlinear.mo",19,9,20,65,1};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta29));
          data->simulationInfo->needToReThrow = 1;
        } else {
          FILE_INFO info = {"/thirdparty/msl/Modelica/Blocks/Nonlinear.mo",19,9,20,65,1};
          omc_assert_withEquationIndexes(threadData, info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta29));
        }
      }
    }
  }
  threadData->lastEquationSolved = 58;
}

OMC_DISABLE_OPT
int artifacts_ct02_exact_two_m00_functionDAE(DATA *data, threadData_t *threadData)
{
  int equationIndexes[1] = {0};
#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_tick(SIM_TIMER_DAE);
#endif

  data->simulationInfo->needToIterate = 0;
  data->simulationInfo->discreteCall = 1;
  artifacts_ct02_exact_two_m00_functionLocalKnownVars(data, threadData);
  static void (*const eqFunctions[13])(DATA*, threadData_t*) = {
    artifacts_ct02_exact_two_m00_eqFunction_47,
    artifacts_ct02_exact_two_m00_eqFunction_48,
    artifacts_ct02_exact_two_m00_eqFunction_49,
    artifacts_ct02_exact_two_m00_eqFunction_50,
    artifacts_ct02_exact_two_m00_eqFunction_51,
    artifacts_ct02_exact_two_m00_eqFunction_52,
    artifacts_ct02_exact_two_m00_eqFunction_53,
    artifacts_ct02_exact_two_m00_eqFunction_54,
    artifacts_ct02_exact_two_m00_eqFunction_55,
    artifacts_ct02_exact_two_m00_eqFunction_56,
    artifacts_ct02_exact_two_m00_eqFunction_57,
    artifacts_ct02_exact_two_m00_eqFunction_59,
    artifacts_ct02_exact_two_m00_eqFunction_58
  };
  
  for (int id = 0; id < 13; id++) {
    eqFunctions[id](data, threadData);
  }
  data->simulationInfo->discreteCall = 0;
  
#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_accumulate(SIM_TIMER_DAE);
#endif
  return 0;
}


int artifacts_ct02_exact_two_m00_functionLocalKnownVars(DATA *data, threadData_t *threadData)
{
  
  return 0;
}

/* forwarded equations */
extern void artifacts_ct02_exact_two_m00_eqFunction_47(DATA* data, threadData_t *threadData);
extern void artifacts_ct02_exact_two_m00_eqFunction_48(DATA* data, threadData_t *threadData);
extern void artifacts_ct02_exact_two_m00_eqFunction_49(DATA* data, threadData_t *threadData);
extern void artifacts_ct02_exact_two_m00_eqFunction_50(DATA* data, threadData_t *threadData);
extern void artifacts_ct02_exact_two_m00_eqFunction_51(DATA* data, threadData_t *threadData);
extern void artifacts_ct02_exact_two_m00_eqFunction_52(DATA* data, threadData_t *threadData);
extern void artifacts_ct02_exact_two_m00_eqFunction_53(DATA* data, threadData_t *threadData);
extern void artifacts_ct02_exact_two_m00_eqFunction_54(DATA* data, threadData_t *threadData);
extern void artifacts_ct02_exact_two_m00_eqFunction_55(DATA* data, threadData_t *threadData);
extern void artifacts_ct02_exact_two_m00_eqFunction_56(DATA* data, threadData_t *threadData);
extern void artifacts_ct02_exact_two_m00_eqFunction_57(DATA* data, threadData_t *threadData);

static void functionODE_system0(DATA *data, threadData_t *threadData)
{
  static void (*const eqFunctions[11])(DATA*, threadData_t*) = {
    artifacts_ct02_exact_two_m00_eqFunction_47,
    artifacts_ct02_exact_two_m00_eqFunction_48,
    artifacts_ct02_exact_two_m00_eqFunction_49,
    artifacts_ct02_exact_two_m00_eqFunction_50,
    artifacts_ct02_exact_two_m00_eqFunction_51,
    artifacts_ct02_exact_two_m00_eqFunction_52,
    artifacts_ct02_exact_two_m00_eqFunction_53,
    artifacts_ct02_exact_two_m00_eqFunction_54,
    artifacts_ct02_exact_two_m00_eqFunction_55,
    artifacts_ct02_exact_two_m00_eqFunction_56,
    artifacts_ct02_exact_two_m00_eqFunction_57
  };
  
  for (int id = 0; id < 11; id++) {
    eqFunctions[id](data, threadData);
  }
}

int artifacts_ct02_exact_two_m00_functionODE(DATA *data, threadData_t *threadData)
{
#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_tick(SIM_TIMER_FUNCTION_ODE);
#endif

  
  data->simulationInfo->callStatistics.functionODE++;
  
  artifacts_ct02_exact_two_m00_functionLocalKnownVars(data, threadData);
  functionODE_system0(data, threadData);

#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_accumulate(SIM_TIMER_FUNCTION_ODE);
#endif

  return 0;
}

/* forward the main in the simulation runtime */
extern int _main_SimulationRuntime(int argc, char **argv, DATA *data, threadData_t *threadData);
extern int _main_OptimizationRuntime(int argc, char **argv, DATA *data, threadData_t *threadData);

#include "artifacts/ct02-exact-two/m00_12jac.h"
#include "artifacts/ct02-exact-two/m00_13opt.h"

struct OpenModelicaGeneratedFunctionCallbacks artifacts_ct02_exact_two_m00_callback = {
  (int (*)(DATA *, threadData_t *, void *)) artifacts_ct02_exact_two_m00_performSimulation,    /* performSimulation */
  (int (*)(DATA *, threadData_t *, void *)) artifacts_ct02_exact_two_m00_performQSSSimulation,    /* performQSSSimulation */
  artifacts_ct02_exact_two_m00_updateContinuousSystem,    /* updateContinuousSystem */
  artifacts_ct02_exact_two_m00_callExternalObjectDestructors,    /* callExternalObjectDestructors */
  NULL,    /* initialNonLinearSystem */
  NULL,    /* initialLinearSystem */
  NULL,    /* initialMixedSystem */
  #if !defined(OMC_NO_STATESELECTION)
  artifacts_ct02_exact_two_m00_initializeStateSets,
  #else
  NULL,
  #endif    /* initializeStateSets */
  artifacts_ct02_exact_two_m00_initializeDAEmodeData,
  artifacts_ct02_exact_two_m00_functionODE,
  artifacts_ct02_exact_two_m00_functionAlgebraics,
  artifacts_ct02_exact_two_m00_functionDAE,
  artifacts_ct02_exact_two_m00_functionLocalKnownVars,
  artifacts_ct02_exact_two_m00_input_function,
  artifacts_ct02_exact_two_m00_input_function_init,
  artifacts_ct02_exact_two_m00_input_function_updateStartValues,
  artifacts_ct02_exact_two_m00_data_function,
  artifacts_ct02_exact_two_m00_output_function,
  artifacts_ct02_exact_two_m00_setc_function,
  artifacts_ct02_exact_two_m00_setb_function,
  artifacts_ct02_exact_two_m00_function_storeDelayed,
  artifacts_ct02_exact_two_m00_function_storeSpatialDistribution,
  artifacts_ct02_exact_two_m00_function_initSpatialDistribution,
  artifacts_ct02_exact_two_m00_updateBoundVariableAttributes,
  artifacts_ct02_exact_two_m00_functionInitialEquations,
  GLOBAL_EQUIDISTANT_HOMOTOPY,
  artifacts_ct02_exact_two_m00_functionInitialEquations_lambda0,
  artifacts_ct02_exact_two_m00_functionRemovedInitialEquations,
  artifacts_ct02_exact_two_m00_updateBoundParameters,
  artifacts_ct02_exact_two_m00_checkForAsserts,
  artifacts_ct02_exact_two_m00_function_ZeroCrossingsEquations,
  artifacts_ct02_exact_two_m00_function_ZeroCrossings,
  artifacts_ct02_exact_two_m00_function_updateRelations,
  artifacts_ct02_exact_two_m00_zeroCrossingDescription,
  artifacts_ct02_exact_two_m00_relationDescription,
  artifacts_ct02_exact_two_m00_function_initSample,
  artifacts_ct02_exact_two_m00_INDEX_JAC_A,
  artifacts_ct02_exact_two_m00_INDEX_JAC_B,
  artifacts_ct02_exact_two_m00_INDEX_JAC_C,
  artifacts_ct02_exact_two_m00_INDEX_JAC_D,
  artifacts_ct02_exact_two_m00_INDEX_JAC_F,
  artifacts_ct02_exact_two_m00_INDEX_JAC_H,
  artifacts_ct02_exact_two_m00_initialAnalyticJacobianA,
  artifacts_ct02_exact_two_m00_initialAnalyticJacobianB,
  artifacts_ct02_exact_two_m00_initialAnalyticJacobianC,
  artifacts_ct02_exact_two_m00_initialAnalyticJacobianD,
  artifacts_ct02_exact_two_m00_initialAnalyticJacobianF,
  artifacts_ct02_exact_two_m00_initialAnalyticJacobianH,
  artifacts_ct02_exact_two_m00_functionJacA_column,
  artifacts_ct02_exact_two_m00_functionJacB_column,
  artifacts_ct02_exact_two_m00_functionJacC_column,
  artifacts_ct02_exact_two_m00_functionJacD_column,
  artifacts_ct02_exact_two_m00_functionJacF_column,
  artifacts_ct02_exact_two_m00_functionJacH_column,
  artifacts_ct02_exact_two_m00_linear_model_frame,
  artifacts_ct02_exact_two_m00_linear_model_datarecovery_frame,
  artifacts_ct02_exact_two_m00_mayer,
  artifacts_ct02_exact_two_m00_lagrange,
  artifacts_ct02_exact_two_m00_getInputVarIndicesInOptimization,
  artifacts_ct02_exact_two_m00_pickUpBoundsForInputsInOptimization,
  artifacts_ct02_exact_two_m00_setInputData,
  artifacts_ct02_exact_two_m00_getTimeGrid,
  artifacts_ct02_exact_two_m00_symbolicInlineSystem,
  artifacts_ct02_exact_two_m00_function_initSynchronous,
  artifacts_ct02_exact_two_m00_function_updateSynchronous,
  artifacts_ct02_exact_two_m00_function_equationsSynchronous,
  artifacts_ct02_exact_two_m00_inputNames,
  artifacts_ct02_exact_two_m00_dataReconciliationInputNames,
  artifacts_ct02_exact_two_m00_dataReconciliationUnmeasuredVariables,
  NULL,
  NULL,
  NULL,
  NULL,
  -1,
  NULL,
  NULL,
  -1

};

#define _OMC_LIT_RESOURCE_0_name_data "ArenaCT03M"
#define _OMC_LIT_RESOURCE_0_dir_data "/repo/artifacts/ct02-exact-two/M"
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_0_name,10,_OMC_LIT_RESOURCE_0_name_data);
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_0_dir,32,_OMC_LIT_RESOURCE_0_dir_data);

#define _OMC_LIT_RESOURCE_1_name_data "IGCInformationMolecules"
#define _OMC_LIT_RESOURCE_1_dir_data "/repo/src/modelica"
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_1_name,23,_OMC_LIT_RESOURCE_1_name_data);
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_1_dir,18,_OMC_LIT_RESOURCE_1_dir_data);

#define _OMC_LIT_RESOURCE_2_name_data "IGCMolecules"
#define _OMC_LIT_RESOURCE_2_dir_data "/repo/src/modelica"
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_2_name,12,_OMC_LIT_RESOURCE_2_name_data);
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_2_dir,18,_OMC_LIT_RESOURCE_2_dir_data);

#define _OMC_LIT_RESOURCE_3_name_data "Modelica"
#define _OMC_LIT_RESOURCE_3_dir_data "/thirdparty/msl/Modelica"
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_3_name,8,_OMC_LIT_RESOURCE_3_name_data);
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_3_dir,24,_OMC_LIT_RESOURCE_3_dir_data);

#define _OMC_LIT_RESOURCE_4_name_data "ModelicaServices"
#define _OMC_LIT_RESOURCE_4_dir_data "/thirdparty/msl/ModelicaServices"
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_4_name,16,_OMC_LIT_RESOURCE_4_name_data);
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_4_dir,32,_OMC_LIT_RESOURCE_4_dir_data);

#define _OMC_LIT_RESOURCE_5_name_data "SystemDynamics"
#define _OMC_LIT_RESOURCE_5_dir_data "/thirdparty/systemdynamics/SystemDynamics"
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_5_name,14,_OMC_LIT_RESOURCE_5_name_data);
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_5_dir,41,_OMC_LIT_RESOURCE_5_dir_data);

static const MMC_DEFSTRUCTLIT(_OMC_LIT_RESOURCES,12,MMC_ARRAY_TAG) {MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_0_name), MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_0_dir), MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_1_name), MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_1_dir), MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_2_name), MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_2_dir), MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_3_name), MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_3_dir), MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_4_name), MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_4_dir), MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_5_name), MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_5_dir)}};
void artifacts_ct02_exact_two_m00_setupDataStruc(DATA *data, threadData_t *threadData)
{
  assertStreamPrint(threadData,0!=data, "Error while initialize Data");
  threadData->localRoots[LOCAL_ROOT_SIMULATION_DATA] = data;
  data->callback = &artifacts_ct02_exact_two_m00_callback;
  OpenModelica_updateUriMapping(threadData, MMC_REFSTRUCTLIT(_OMC_LIT_RESOURCES));
  data->modelData->modelName = "ArenaCT03M.CT03M_18247fc54a54";
  data->modelData->modelFilePrefix = "artifacts/ct02-exact-two/m00";
  data->modelData->modelFileName = "native.mo";
  data->modelData->resultFileName = NULL;
  data->modelData->modelDir = "/repo/artifacts/ct02-exact-two/M";
  data->modelData->modelGUID = "{5d58c239-bfa1-42be-a095-d84e087563ab}";
  #if defined(OPENMODELICA_XML_FROM_FILE_AT_RUNTIME)
  data->modelData->initXMLData = NULL;
  data->modelData->modelDataXml.infoXMLData = NULL;
  #else
  #if defined(_MSC_VER) /* handle joke compilers */
  {
  /* for MSVC we encode a string like char x[] = {'a', 'b', 'c', '\0'} */
  /* because the string constant limit is 65535 bytes */
  static const char contents_init[] =
    #include "artifacts/ct02-exact-two/m00_init.c"
    ;
  static const char contents_info[] =
    #include "artifacts/ct02-exact-two/m00_info.c"
    ;
    data->modelData->initXMLData = contents_init;
    data->modelData->modelDataXml.infoXMLData = contents_info;
  }
  #else /* handle real compilers */
  data->modelData->initXMLData =
  #include "artifacts/ct02-exact-two/m00_init.c"
    ;
  data->modelData->modelDataXml.infoXMLData =
  #include "artifacts/ct02-exact-two/m00_info.c"
    ;
  #endif /* defined(_MSC_VER) */
  #endif /* defined(OPENMODELICA_XML_FROM_FILE_AT_RUNTIME) */
  data->modelData->modelDataXml.fileName = "artifacts/ct02-exact-two/m00_info.json";
  data->modelData->resourcesDir = NULL;
  data->modelData->runTestsuite = 0;
  data->modelData->nStatesArray = 4;
  data->modelData->nDiscreteReal = 0;
  data->modelData->nVariablesRealArray = 19;
  data->modelData->nVariablesIntegerArray = 0;
  data->modelData->nVariablesBooleanArray = 3;
  data->modelData->nVariablesStringArray = 0;
  data->modelData->nParametersRealArray = 31;
  data->modelData->nParametersIntegerArray = 7;
  data->modelData->nParametersBooleanArray = 8;
  data->modelData->nParametersStringArray = 0;
  data->modelData->nParametersReal = 31;
  data->modelData->nParametersInteger = 7;
  data->modelData->nParametersBoolean = 8;
  data->modelData->nParametersString = 0;
  data->modelData->nAliasRealArray = 77;
  data->modelData->nAliasIntegerArray = 0;
  data->modelData->nAliasBooleanArray = 0;
  data->modelData->nAliasStringArray = 0;
  data->modelData->nInputVars = 0;
  data->modelData->nOutputVars = 0;
  data->modelData->nZeroCrossings = 1;
  data->modelData->nSamples = 0;
  data->modelData->nRelations = 1;
  data->modelData->nMathEvents = 0;
  data->modelData->nExtObjs = 0;
  data->modelData->modelDataXml.modelInfoXmlLength = 0;
  data->modelData->modelDataXml.nFunctions = 0;
  data->modelData->modelDataXml.nProfileBlocks = 0;
  data->modelData->modelDataXml.nEquations = 109;
  data->modelData->nMixedSystems = 0;
  data->modelData->nLinearSystems = 0;
  data->modelData->nNonLinearSystems = 0;
  data->modelData->nStateSets = 0;
  data->modelData->nJacobians = 6;
  data->modelData->nOptimizeConstraints = 0;
  data->modelData->nOptimizeFinalConstraints = 0;
  data->modelData->nDelayExpressions = 0;
  data->modelData->nBaseClocks = 0;
  data->modelData->nSpatialDistributions = 0;
  data->modelData->nSensitivityVars = 0;
  data->modelData->nSensitivityParamVars = 0;
  data->modelData->nSetcVars = 0;
  data->modelData->ndataReconVars = 0;
  data->modelData->nSetbVars = 0;
  data->modelData->nRelatedBoundaryConditions = 0;
  data->modelData->linearizationDumpLanguage = OMC_LINEARIZE_DUMP_LANGUAGE_MODELICA;
}

static int rml_execution_failed()
{
  fflush(NULL);
  fprintf(stderr, "Execution failed!\n");
  fflush(NULL);
  return 1;
}


#if defined(__MINGW32__) || defined(_MSC_VER)

#if !defined(_UNICODE)
#define _UNICODE
#endif
#if !defined(UNICODE)
#define UNICODE
#endif

#include <windows.h>
char** omc_fixWindowsArgv(int argc, wchar_t **wargv)
{
  char** newargv;
  /* Support for non-ASCII characters
  * Read the unicode command line arguments and translate it to char*
  */
  newargv = (char**)malloc(argc*sizeof(char*));
  for (int i = 0; i < argc; i++) {
    newargv[i] = omc_wchar_to_multibyte_str(wargv[i]);
  }
  return newargv;
}

#define OMC_MAIN wmain
#define OMC_CHAR wchar_t
#define OMC_EXPORT __declspec(dllexport) extern

#else
#define omc_fixWindowsArgv(N, A) (A)
#define OMC_MAIN main
#define OMC_CHAR char
#define OMC_EXPORT extern
#endif

#if defined(threadData)
#undef threadData
#endif
/* call the simulation runtime main from our main! */
#if defined(OMC_DLL_MAIN_DEFINE)
OMC_EXPORT int omcDllMain(int argc, OMC_CHAR **argv)
#else
int OMC_MAIN(int argc, OMC_CHAR** argv)
#endif
{
  char** newargv = omc_fixWindowsArgv(argc, argv);
  /*
    Set the error functions to be used for simulation.
    The default value for them is 'functions' version. Change it here to 'simulation' versions
  */
  omc_assert = omc_assert_simulation;
  omc_assert_withEquationIndexes = omc_assert_simulation_withEquationIndexes;

  omc_assert_warning_withEquationIndexes = omc_assert_warning_simulation_withEquationIndexes;
  omc_assert_warning = omc_assert_warning_simulation;
  omc_terminate = omc_terminate_simulation;
  omc_throw = omc_throw_simulation;

  int res;
  DATA data;
  MODEL_DATA modelData;
  SIMULATION_INFO simInfo;
  data.modelData = &modelData;
  data.simulationInfo = &simInfo;
  measure_time_flag = 0;
  compiledInDAEMode = 0;
  compiledWithSymSolver = 0;
  MMC_INIT(0);
  omc_alloc_interface.init();
  {
    MMC_TRY_TOP()
  
    MMC_TRY_STACK()
  
    artifacts_ct02_exact_two_m00_setupDataStruc(&data, threadData);
    res = _main_initRuntimeAndSimulation(argc, newargv, &data, threadData);
    if(res == 0) {
      if (omc_flag[FLAG_MOO_OPTIMIZATION]) {
        res = _main_OptimizationRuntime(argc, newargv, &data, threadData);
      } else {
        res = _main_SimulationRuntime(argc, newargv, &data, threadData);
      }
    }
    
    MMC_ELSE()
    rml_execution_failed();
    fprintf(stderr, "Stack overflow detected and was not caught.\nSend us a bug report at https://trac.openmodelica.org/OpenModelica/newticket\n    Include the following trace:\n");
    printStacktraceMessages();
    fflush(NULL);
    return 1;
    MMC_CATCH_STACK()
    
    MMC_CATCH_TOP(return rml_execution_failed());
  }

  fflush(NULL);
  return res;
}

#ifdef __cplusplus
}
#endif


