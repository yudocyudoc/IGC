/* update bound parameters and variable attributes (start, nominal, min, max) */
#include "artifacts/ct02-exact-two/m00_model.h"
#if defined(__cplusplus)
extern "C" {
#endif


/*
equation index: 60
type: SIMPLE_ASSIGN
$START.report0.reportFilter.y = report0.reportFilter.y_start
*/
static void artifacts_ct02_exact_two_m00_eqFunction_60(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,60};
  ((modelica_real *)((data->modelData->realVarsData[3] /* report0.reportFilter.y STATE(1) */).attribute .start.data))[0] = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[29]] /* report0.reportFilter.y_start PARAM */);
    (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[3]] /* report0.reportFilter.y STATE(1) */) = ((modelica_real *)((data->modelData->realVarsData[3] /* report0.reportFilter.y STATE(1) */).attribute .start.data))[0];
    infoStreamPrint(OMC_LOG_INIT_V, 0, "updated start value: %s(start=%g)", data->modelData->realVarsData[3].info /* report0.reportFilter.y */.name, (modelica_real) (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[3]] /* report0.reportFilter.y STATE(1) */));
  threadData->lastEquationSolved = 60;
}

/*
equation index: 61
type: SIMPLE_ASSIGN
$START.receipt0.deliveries.Integrator1.y = receipt0.deliveries.Integrator1.y_start
*/
static void artifacts_ct02_exact_two_m00_eqFunction_61(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,61};
  ((modelica_real *)((data->modelData->realVarsData[2] /* receipt0.deliveries.Integrator1.y STATE(1) */).attribute .start.data))[0] = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[25]] /* receipt0.deliveries.Integrator1.y_start PARAM */);
    (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[2]] /* receipt0.deliveries.Integrator1.y STATE(1) */) = ((modelica_real *)((data->modelData->realVarsData[2] /* receipt0.deliveries.Integrator1.y STATE(1) */).attribute .start.data))[0];
    infoStreamPrint(OMC_LOG_INIT_V, 0, "updated start value: %s(start=%g)", data->modelData->realVarsData[2].info /* receipt0.deliveries.Integrator1.y */.name, (modelica_real) (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[2]] /* receipt0.deliveries.Integrator1.y STATE(1) */));
  threadData->lastEquationSolved = 61;
}

/*
equation index: 62
type: SIMPLE_ASSIGN
$START.dispatch0.stock.Integrator1.y = dispatch0.stock.Integrator1.y_start
*/
static void artifacts_ct02_exact_two_m00_eqFunction_62(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,62};
  ((modelica_real *)((data->modelData->realVarsData[0] /* dispatch0.stock.Integrator1.y STATE(1) */).attribute .start.data))[0] = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[10]] /* dispatch0.stock.Integrator1.y_start PARAM */);
    (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[0]] /* dispatch0.stock.Integrator1.y STATE(1) */) = ((modelica_real *)((data->modelData->realVarsData[0] /* dispatch0.stock.Integrator1.y STATE(1) */).attribute .start.data))[0];
    infoStreamPrint(OMC_LOG_INIT_V, 0, "updated start value: %s(start=%g)", data->modelData->realVarsData[0].info /* dispatch0.stock.Integrator1.y */.name, (modelica_real) (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[0]] /* dispatch0.stock.Integrator1.y STATE(1) */));
  threadData->lastEquationSolved = 62;
}

/*
equation index: 63
type: SIMPLE_ASSIGN
$START.preparation0.stock.Integrator1.y = preparation0.stock.Integrator1.y_start
*/
static void artifacts_ct02_exact_two_m00_eqFunction_63(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,63};
  ((modelica_real *)((data->modelData->realVarsData[1] /* preparation0.stock.Integrator1.y STATE(1) */).attribute .start.data))[0] = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[22]] /* preparation0.stock.Integrator1.y_start PARAM */);
    (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[1]] /* preparation0.stock.Integrator1.y STATE(1) */) = ((modelica_real *)((data->modelData->realVarsData[1] /* preparation0.stock.Integrator1.y STATE(1) */).attribute .start.data))[0];
    infoStreamPrint(OMC_LOG_INIT_V, 0, "updated start value: %s(start=%g)", data->modelData->realVarsData[1].info /* preparation0.stock.Integrator1.y */.name, (modelica_real) (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[1]] /* preparation0.stock.Integrator1.y STATE(1) */));
  threadData->lastEquationSolved = 63;
}
OMC_DISABLE_OPT
int artifacts_ct02_exact_two_m00_updateBoundVariableAttributes(DATA *data, threadData_t *threadData)
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
  artifacts_ct02_exact_two_m00_eqFunction_60(data, threadData);
  artifacts_ct02_exact_two_m00_eqFunction_61(data, threadData);
  artifacts_ct02_exact_two_m00_eqFunction_62(data, threadData);
  artifacts_ct02_exact_two_m00_eqFunction_63(data, threadData);
  messageClose(OMC_LOG_INIT);
  
  return 0;
}

void artifacts_ct02_exact_two_m00_updateBoundParameters_0(DATA *data, threadData_t *threadData);

/*
equation index: 65
type: SIMPLE_ASSIGN
report0.reportFilter.T = report0.reportResponseTime
*/
OMC_DISABLE_OPT
static void artifacts_ct02_exact_two_m00_eqFunction_65(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,65};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[27]] /* report0.reportFilter.T PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[30]] /* report0.reportResponseTime PARAM */);
  threadData->lastEquationSolved = 65;
}

/*
equation index: 66
type: SIMPLE_ASSIGN
receipt0.deliveries.Integrator1.y_start = receipt0.deliveries.x0
*/
OMC_DISABLE_OPT
static void artifacts_ct02_exact_two_m00_eqFunction_66(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,66};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[25]] /* receipt0.deliveries.Integrator1.y_start PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[26]] /* receipt0.deliveries.x0 PARAM */);
  threadData->lastEquationSolved = 66;
}

/*
equation index: 70
type: SIMPLE_ASSIGN
dispatch0.response.k = 1.0 / dispatch0.responseTime
*/
OMC_DISABLE_OPT
static void artifacts_ct02_exact_two_m00_eqFunction_70(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,70};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[5]] /* dispatch0.response.k PARAM */) = DIVISION_SIM(1.0,(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[6]] /* dispatch0.responseTime PARAM */),"dispatch0.responseTime",equationIndexes);
  threadData->lastEquationSolved = 70;
}

/*
equation index: 73
type: SIMPLE_ASSIGN
dispatch0.release.Limiter1.uMin = dispatch0.release.minFlow
*/
OMC_DISABLE_OPT
static void artifacts_ct02_exact_two_m00_eqFunction_73(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,73};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[2]] /* dispatch0.release.Limiter1.uMin PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[4]] /* dispatch0.release.minFlow PARAM */);
  threadData->lastEquationSolved = 73;
}

/*
equation index: 74
type: SIMPLE_ASSIGN
dispatch0.release.maxFlow = dispatch0.maxThroughput
*/
OMC_DISABLE_OPT
static void artifacts_ct02_exact_two_m00_eqFunction_74(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,74};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[3]] /* dispatch0.release.maxFlow PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[0]] /* dispatch0.maxThroughput PARAM */);
  threadData->lastEquationSolved = 74;
}

/*
equation index: 75
type: SIMPLE_ASSIGN
dispatch0.release.Limiter1.uMax = dispatch0.release.maxFlow
*/
OMC_DISABLE_OPT
static void artifacts_ct02_exact_two_m00_eqFunction_75(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,75};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[1]] /* dispatch0.release.Limiter1.uMax PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[3]] /* dispatch0.release.maxFlow PARAM */);
  threadData->lastEquationSolved = 75;
}

/*
equation index: 76
type: SIMPLE_ASSIGN
dispatch0.stock.Integrator1.y_start = dispatch0.stock.x0
*/
OMC_DISABLE_OPT
static void artifacts_ct02_exact_two_m00_eqFunction_76(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,76};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[10]] /* dispatch0.stock.Integrator1.y_start PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[11]] /* dispatch0.stock.x0 PARAM */);
  threadData->lastEquationSolved = 76;
}

/*
equation index: 80
type: SIMPLE_ASSIGN
preparation0.response.k = 1.0 / preparation0.responseTime
*/
OMC_DISABLE_OPT
static void artifacts_ct02_exact_two_m00_eqFunction_80(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,80};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[17]] /* preparation0.response.k PARAM */) = DIVISION_SIM(1.0,(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[18]] /* preparation0.responseTime PARAM */),"preparation0.responseTime",equationIndexes);
  threadData->lastEquationSolved = 80;
}

/*
equation index: 83
type: SIMPLE_ASSIGN
preparation0.release.Limiter1.uMin = preparation0.release.minFlow
*/
OMC_DISABLE_OPT
static void artifacts_ct02_exact_two_m00_eqFunction_83(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,83};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[14]] /* preparation0.release.Limiter1.uMin PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[16]] /* preparation0.release.minFlow PARAM */);
  threadData->lastEquationSolved = 83;
}

/*
equation index: 84
type: SIMPLE_ASSIGN
preparation0.release.maxFlow = preparation0.maxThroughput
*/
OMC_DISABLE_OPT
static void artifacts_ct02_exact_two_m00_eqFunction_84(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,84};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[15]] /* preparation0.release.maxFlow PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[12]] /* preparation0.maxThroughput PARAM */);
  threadData->lastEquationSolved = 84;
}

/*
equation index: 85
type: SIMPLE_ASSIGN
preparation0.release.Limiter1.uMax = preparation0.release.maxFlow
*/
OMC_DISABLE_OPT
static void artifacts_ct02_exact_two_m00_eqFunction_85(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,85};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[13]] /* preparation0.release.Limiter1.uMax PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[15]] /* preparation0.release.maxFlow PARAM */);
  threadData->lastEquationSolved = 85;
}

/*
equation index: 86
type: SIMPLE_ASSIGN
preparation0.stock.Integrator1.y_start = preparation0.stock.x0
*/
OMC_DISABLE_OPT
static void artifacts_ct02_exact_two_m00_eqFunction_86(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,86};
  (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[22]] /* preparation0.stock.Integrator1.y_start PARAM */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[23]] /* preparation0.stock.x0 PARAM */);
  threadData->lastEquationSolved = 86;
}
extern void artifacts_ct02_exact_two_m00_eqFunction_7(DATA *data, threadData_t *threadData);

extern void artifacts_ct02_exact_two_m00_eqFunction_6(DATA *data, threadData_t *threadData);

extern void artifacts_ct02_exact_two_m00_eqFunction_5(DATA *data, threadData_t *threadData);

extern void artifacts_ct02_exact_two_m00_eqFunction_4(DATA *data, threadData_t *threadData);

extern void artifacts_ct02_exact_two_m00_eqFunction_3(DATA *data, threadData_t *threadData);

extern void artifacts_ct02_exact_two_m00_eqFunction_2(DATA *data, threadData_t *threadData);

extern void artifacts_ct02_exact_two_m00_eqFunction_1(DATA *data, threadData_t *threadData);


/*
equation index: 97
type: ALGORITHM

  assert(report0.reportFilter.initType >= Modelica.Blocks.Types.Init.NoInit and report0.reportFilter.initType <= Modelica.Blocks.Types.Init.InitialOutput, "Variable violating min/max constraint: Modelica.Blocks.Types.Init.NoInit <= report0.reportFilter.initType <= Modelica.Blocks.Types.Init.InitialOutput, has value: " + String(report0.reportFilter.initType, "d"));
*/
OMC_DISABLE_OPT
static void artifacts_ct02_exact_two_m00_eqFunction_97(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,97};
  modelica_boolean tmp0;
  modelica_boolean tmp1;
  static const MMC_DEFSTRINGLIT(tmp2,162,"Variable violating min/max constraint: Modelica.Blocks.Types.Init.NoInit <= report0.reportFilter.initType <= Modelica.Blocks.Types.Init.InitialOutput, has value: ");
  modelica_string tmp3;
  modelica_metatype tmpMeta4;
  static int tmp5 = 0;
  if(!tmp5)
  {
    tmp0 = GreaterEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[6]] /* report0.reportFilter.initType PARAM */),1);
    tmp1 = LessEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[6]] /* report0.reportFilter.initType PARAM */),4);
    if(!(tmp0 && tmp1))
    {
      tmp3 = modelica_integer_to_modelica_string_format((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[6]] /* report0.reportFilter.initType PARAM */), (modelica_string) mmc_strings_len1[100]);
      tmpMeta4 = stringAppend(MMC_REFSTRINGLIT(tmp2),tmp3);
      {
        const char* assert_cond = "(report0.reportFilter.initType >= Modelica.Blocks.Types.Init.NoInit and report0.reportFilter.initType <= Modelica.Blocks.Types.Init.InitialOutput)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/thirdparty/msl/Modelica/Blocks/Continuous.mo",355,5,357,40,1};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta4));
        } else {
          FILE_INFO info = {"/thirdparty/msl/Modelica/Blocks/Continuous.mo",355,5,357,40,1};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta4));
        }
      }
      tmp5 = 1;
    }
  }
  threadData->lastEquationSolved = 97;
}

/*
equation index: 98
type: ALGORITHM

  assert(report0.reportResponseTime >= 1e-9, "Variable violating min constraint: 1e-9 <= report0.reportResponseTime, has value: " + String(report0.reportResponseTime, "g"));
*/
OMC_DISABLE_OPT
static void artifacts_ct02_exact_two_m00_eqFunction_98(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,98};
  modelica_boolean tmp6;
  static const MMC_DEFSTRINGLIT(tmp7,82,"Variable violating min constraint: 1e-9 <= report0.reportResponseTime, has value: ");
  modelica_string tmp8;
  modelica_metatype tmpMeta9;
  static int tmp10 = 0;
  if(!tmp10)
  {
    tmp6 = GreaterEq((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[30]] /* report0.reportResponseTime PARAM */),1e-9);
    if(!tmp6)
    {
      tmp8 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[30]] /* report0.reportResponseTime PARAM */), (modelica_string) mmc_strings_len1[103]);
      tmpMeta9 = stringAppend(MMC_REFSTRINGLIT(tmp7),tmp8);
      {
        const char* assert_cond = "(report0.reportResponseTime >= 1e-9)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/repo/src/modelica/IGCInformationMolecules.mo",5,5,5,52,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta9));
        } else {
          FILE_INFO info = {"/repo/src/modelica/IGCInformationMolecules.mo",5,5,5,52,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta9));
        }
      }
      tmp10 = 1;
    }
  }
  threadData->lastEquationSolved = 98;
}

/*
equation index: 99
type: ALGORITHM

  assert(receipt0.deliveries.Integrator1.initType >= Modelica.Blocks.Types.Init.NoInit and receipt0.deliveries.Integrator1.initType <= Modelica.Blocks.Types.Init.InitialOutput, "Variable violating min/max constraint: Modelica.Blocks.Types.Init.NoInit <= receipt0.deliveries.Integrator1.initType <= Modelica.Blocks.Types.Init.InitialOutput, has value: " + String(receipt0.deliveries.Integrator1.initType, "d"));
*/
OMC_DISABLE_OPT
static void artifacts_ct02_exact_two_m00_eqFunction_99(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,99};
  modelica_boolean tmp11;
  modelica_boolean tmp12;
  static const MMC_DEFSTRINGLIT(tmp13,173,"Variable violating min/max constraint: Modelica.Blocks.Types.Init.NoInit <= receipt0.deliveries.Integrator1.initType <= Modelica.Blocks.Types.Init.InitialOutput, has value: ");
  modelica_string tmp14;
  modelica_metatype tmpMeta15;
  static int tmp16 = 0;
  if(!tmp16)
  {
    tmp11 = GreaterEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[5]] /* receipt0.deliveries.Integrator1.initType PARAM */),1);
    tmp12 = LessEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[5]] /* receipt0.deliveries.Integrator1.initType PARAM */),4);
    if(!(tmp11 && tmp12))
    {
      tmp14 = modelica_integer_to_modelica_string_format((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[5]] /* receipt0.deliveries.Integrator1.initType PARAM */), (modelica_string) mmc_strings_len1[100]);
      tmpMeta15 = stringAppend(MMC_REFSTRINGLIT(tmp13),tmp14);
      {
        const char* assert_cond = "(receipt0.deliveries.Integrator1.initType >= Modelica.Blocks.Types.Init.NoInit and receipt0.deliveries.Integrator1.initType <= Modelica.Blocks.Types.Init.InitialOutput)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/thirdparty/msl/Modelica/Blocks/Continuous.mo",19,5,21,40,1};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta15));
        } else {
          FILE_INFO info = {"/thirdparty/msl/Modelica/Blocks/Continuous.mo",19,5,21,40,1};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta15));
        }
      }
      tmp16 = 1;
    }
  }
  threadData->lastEquationSolved = 99;
}

/*
equation index: 100
type: ALGORITHM

  assert(dispatch0.responseTime >= 1e-9, "Variable violating min constraint: 1e-9 <= dispatch0.responseTime, has value: " + String(dispatch0.responseTime, "g"));
*/
OMC_DISABLE_OPT
static void artifacts_ct02_exact_two_m00_eqFunction_100(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,100};
  modelica_boolean tmp17;
  static const MMC_DEFSTRINGLIT(tmp18,78,"Variable violating min constraint: 1e-9 <= dispatch0.responseTime, has value: ");
  modelica_string tmp19;
  modelica_metatype tmpMeta20;
  static int tmp21 = 0;
  if(!tmp21)
  {
    tmp17 = GreaterEq((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[6]] /* dispatch0.responseTime PARAM */),1e-9);
    if(!tmp17)
    {
      tmp19 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[6]] /* dispatch0.responseTime PARAM */), (modelica_string) mmc_strings_len1[103]);
      tmpMeta20 = stringAppend(MMC_REFSTRINGLIT(tmp18),tmp19);
      {
        const char* assert_cond = "(dispatch0.responseTime >= 1e-9)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/repo/src/modelica/IGCMolecules.mo",17,5,17,42,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta20));
        } else {
          FILE_INFO info = {"/repo/src/modelica/IGCMolecules.mo",17,5,17,42,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta20));
        }
      }
      tmp21 = 1;
    }
  }
  threadData->lastEquationSolved = 100;
}

/*
equation index: 101
type: ALGORITHM

  assert(dispatch0.release.Limiter1.homotopyType >= Modelica.Blocks.Types.LimiterHomotopy.NoHomotopy and dispatch0.release.Limiter1.homotopyType <= Modelica.Blocks.Types.LimiterHomotopy.LowerLimit, "Variable violating min/max constraint: Modelica.Blocks.Types.LimiterHomotopy.NoHomotopy <= dispatch0.release.Limiter1.homotopyType <= Modelica.Blocks.Types.LimiterHomotopy.LowerLimit, has value: " + String(dispatch0.release.Limiter1.homotopyType, "d"));
*/
OMC_DISABLE_OPT
static void artifacts_ct02_exact_two_m00_eqFunction_101(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,101};
  modelica_boolean tmp22;
  modelica_boolean tmp23;
  static const MMC_DEFSTRINGLIT(tmp24,195,"Variable violating min/max constraint: Modelica.Blocks.Types.LimiterHomotopy.NoHomotopy <= dispatch0.release.Limiter1.homotopyType <= Modelica.Blocks.Types.LimiterHomotopy.LowerLimit, has value: ");
  modelica_string tmp25;
  modelica_metatype tmpMeta26;
  static int tmp27 = 0;
  if(!tmp27)
  {
    tmp22 = GreaterEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[0]] /* dispatch0.release.Limiter1.homotopyType PARAM */),1);
    tmp23 = LessEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[0]] /* dispatch0.release.Limiter1.homotopyType PARAM */),4);
    if(!(tmp22 && tmp23))
    {
      tmp25 = modelica_integer_to_modelica_string_format((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[0]] /* dispatch0.release.Limiter1.homotopyType PARAM */), (modelica_string) mmc_strings_len1[100]);
      tmpMeta26 = stringAppend(MMC_REFSTRINGLIT(tmp24),tmp25);
      {
        const char* assert_cond = "(dispatch0.release.Limiter1.homotopyType >= Modelica.Blocks.Types.LimiterHomotopy.NoHomotopy and dispatch0.release.Limiter1.homotopyType <= Modelica.Blocks.Types.LimiterHomotopy.LowerLimit)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/thirdparty/msl/Modelica/Blocks/Nonlinear.mo",12,9,13,69,1};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta26));
        } else {
          FILE_INFO info = {"/thirdparty/msl/Modelica/Blocks/Nonlinear.mo",12,9,13,69,1};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta26));
        }
      }
      tmp27 = 1;
    }
  }
  threadData->lastEquationSolved = 101;
}

/*
equation index: 102
type: ALGORITHM

  assert(dispatch0.maxThroughput >= 0.0, "Variable violating min constraint: 0.0 <= dispatch0.maxThroughput, has value: " + String(dispatch0.maxThroughput, "g"));
*/
OMC_DISABLE_OPT
static void artifacts_ct02_exact_two_m00_eqFunction_102(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,102};
  modelica_boolean tmp28;
  static const MMC_DEFSTRINGLIT(tmp29,78,"Variable violating min constraint: 0.0 <= dispatch0.maxThroughput, has value: ");
  modelica_string tmp30;
  modelica_metatype tmpMeta31;
  static int tmp32 = 0;
  if(!tmp32)
  {
    tmp28 = GreaterEq((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[0]] /* dispatch0.maxThroughput PARAM */),0.0);
    if(!tmp28)
    {
      tmp30 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[0]] /* dispatch0.maxThroughput PARAM */), (modelica_string) mmc_strings_len1[103]);
      tmpMeta31 = stringAppend(MMC_REFSTRINGLIT(tmp29),tmp30);
      {
        const char* assert_cond = "(dispatch0.maxThroughput >= 0.0)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/repo/src/modelica/IGCMolecules.mo",16,5,16,40,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta31));
        } else {
          FILE_INFO info = {"/repo/src/modelica/IGCMolecules.mo",16,5,16,40,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta31));
        }
      }
      tmp32 = 1;
    }
  }
  threadData->lastEquationSolved = 102;
}

/*
equation index: 103
type: ALGORITHM

  assert(dispatch0.stock.Integrator1.initType >= Modelica.Blocks.Types.Init.NoInit and dispatch0.stock.Integrator1.initType <= Modelica.Blocks.Types.Init.InitialOutput, "Variable violating min/max constraint: Modelica.Blocks.Types.Init.NoInit <= dispatch0.stock.Integrator1.initType <= Modelica.Blocks.Types.Init.InitialOutput, has value: " + String(dispatch0.stock.Integrator1.initType, "d"));
*/
OMC_DISABLE_OPT
static void artifacts_ct02_exact_two_m00_eqFunction_103(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,103};
  modelica_boolean tmp33;
  modelica_boolean tmp34;
  static const MMC_DEFSTRINGLIT(tmp35,169,"Variable violating min/max constraint: Modelica.Blocks.Types.Init.NoInit <= dispatch0.stock.Integrator1.initType <= Modelica.Blocks.Types.Init.InitialOutput, has value: ");
  modelica_string tmp36;
  modelica_metatype tmpMeta37;
  static int tmp38 = 0;
  if(!tmp38)
  {
    tmp33 = GreaterEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[1]] /* dispatch0.stock.Integrator1.initType PARAM */),1);
    tmp34 = LessEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[1]] /* dispatch0.stock.Integrator1.initType PARAM */),4);
    if(!(tmp33 && tmp34))
    {
      tmp36 = modelica_integer_to_modelica_string_format((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[1]] /* dispatch0.stock.Integrator1.initType PARAM */), (modelica_string) mmc_strings_len1[100]);
      tmpMeta37 = stringAppend(MMC_REFSTRINGLIT(tmp35),tmp36);
      {
        const char* assert_cond = "(dispatch0.stock.Integrator1.initType >= Modelica.Blocks.Types.Init.NoInit and dispatch0.stock.Integrator1.initType <= Modelica.Blocks.Types.Init.InitialOutput)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/thirdparty/msl/Modelica/Blocks/Continuous.mo",19,5,21,40,1};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta37));
        } else {
          FILE_INFO info = {"/thirdparty/msl/Modelica/Blocks/Continuous.mo",19,5,21,40,1};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta37));
        }
      }
      tmp38 = 1;
    }
  }
  threadData->lastEquationSolved = 103;
}

/*
equation index: 104
type: ALGORITHM

  assert(preparation0.responseTime >= 1e-9, "Variable violating min constraint: 1e-9 <= preparation0.responseTime, has value: " + String(preparation0.responseTime, "g"));
*/
OMC_DISABLE_OPT
static void artifacts_ct02_exact_two_m00_eqFunction_104(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,104};
  modelica_boolean tmp39;
  static const MMC_DEFSTRINGLIT(tmp40,81,"Variable violating min constraint: 1e-9 <= preparation0.responseTime, has value: ");
  modelica_string tmp41;
  modelica_metatype tmpMeta42;
  static int tmp43 = 0;
  if(!tmp43)
  {
    tmp39 = GreaterEq((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[18]] /* preparation0.responseTime PARAM */),1e-9);
    if(!tmp39)
    {
      tmp41 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[18]] /* preparation0.responseTime PARAM */), (modelica_string) mmc_strings_len1[103]);
      tmpMeta42 = stringAppend(MMC_REFSTRINGLIT(tmp40),tmp41);
      {
        const char* assert_cond = "(preparation0.responseTime >= 1e-9)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/repo/src/modelica/IGCMolecules.mo",17,5,17,42,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta42));
        } else {
          FILE_INFO info = {"/repo/src/modelica/IGCMolecules.mo",17,5,17,42,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta42));
        }
      }
      tmp43 = 1;
    }
  }
  threadData->lastEquationSolved = 104;
}

/*
equation index: 105
type: ALGORITHM

  assert(preparation0.release.Limiter1.homotopyType >= Modelica.Blocks.Types.LimiterHomotopy.NoHomotopy and preparation0.release.Limiter1.homotopyType <= Modelica.Blocks.Types.LimiterHomotopy.LowerLimit, "Variable violating min/max constraint: Modelica.Blocks.Types.LimiterHomotopy.NoHomotopy <= preparation0.release.Limiter1.homotopyType <= Modelica.Blocks.Types.LimiterHomotopy.LowerLimit, has value: " + String(preparation0.release.Limiter1.homotopyType, "d"));
*/
OMC_DISABLE_OPT
static void artifacts_ct02_exact_two_m00_eqFunction_105(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,105};
  modelica_boolean tmp44;
  modelica_boolean tmp45;
  static const MMC_DEFSTRINGLIT(tmp46,198,"Variable violating min/max constraint: Modelica.Blocks.Types.LimiterHomotopy.NoHomotopy <= preparation0.release.Limiter1.homotopyType <= Modelica.Blocks.Types.LimiterHomotopy.LowerLimit, has value: ");
  modelica_string tmp47;
  modelica_metatype tmpMeta48;
  static int tmp49 = 0;
  if(!tmp49)
  {
    tmp44 = GreaterEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[2]] /* preparation0.release.Limiter1.homotopyType PARAM */),1);
    tmp45 = LessEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[2]] /* preparation0.release.Limiter1.homotopyType PARAM */),4);
    if(!(tmp44 && tmp45))
    {
      tmp47 = modelica_integer_to_modelica_string_format((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[2]] /* preparation0.release.Limiter1.homotopyType PARAM */), (modelica_string) mmc_strings_len1[100]);
      tmpMeta48 = stringAppend(MMC_REFSTRINGLIT(tmp46),tmp47);
      {
        const char* assert_cond = "(preparation0.release.Limiter1.homotopyType >= Modelica.Blocks.Types.LimiterHomotopy.NoHomotopy and preparation0.release.Limiter1.homotopyType <= Modelica.Blocks.Types.LimiterHomotopy.LowerLimit)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/thirdparty/msl/Modelica/Blocks/Nonlinear.mo",12,9,13,69,1};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta48));
        } else {
          FILE_INFO info = {"/thirdparty/msl/Modelica/Blocks/Nonlinear.mo",12,9,13,69,1};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta48));
        }
      }
      tmp49 = 1;
    }
  }
  threadData->lastEquationSolved = 105;
}

/*
equation index: 106
type: ALGORITHM

  assert(preparation0.maxThroughput >= 0.0, "Variable violating min constraint: 0.0 <= preparation0.maxThroughput, has value: " + String(preparation0.maxThroughput, "g"));
*/
OMC_DISABLE_OPT
static void artifacts_ct02_exact_two_m00_eqFunction_106(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,106};
  modelica_boolean tmp50;
  static const MMC_DEFSTRINGLIT(tmp51,81,"Variable violating min constraint: 0.0 <= preparation0.maxThroughput, has value: ");
  modelica_string tmp52;
  modelica_metatype tmpMeta53;
  static int tmp54 = 0;
  if(!tmp54)
  {
    tmp50 = GreaterEq((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[12]] /* preparation0.maxThroughput PARAM */),0.0);
    if(!tmp50)
    {
      tmp52 = modelica_real_to_modelica_string_format((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[12]] /* preparation0.maxThroughput PARAM */), (modelica_string) mmc_strings_len1[103]);
      tmpMeta53 = stringAppend(MMC_REFSTRINGLIT(tmp51),tmp52);
      {
        const char* assert_cond = "(preparation0.maxThroughput >= 0.0)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/repo/src/modelica/IGCMolecules.mo",16,5,16,40,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta53));
        } else {
          FILE_INFO info = {"/repo/src/modelica/IGCMolecules.mo",16,5,16,40,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta53));
        }
      }
      tmp54 = 1;
    }
  }
  threadData->lastEquationSolved = 106;
}

/*
equation index: 107
type: ALGORITHM

  assert(preparation0.stock.Integrator1.initType >= Modelica.Blocks.Types.Init.NoInit and preparation0.stock.Integrator1.initType <= Modelica.Blocks.Types.Init.InitialOutput, "Variable violating min/max constraint: Modelica.Blocks.Types.Init.NoInit <= preparation0.stock.Integrator1.initType <= Modelica.Blocks.Types.Init.InitialOutput, has value: " + String(preparation0.stock.Integrator1.initType, "d"));
*/
OMC_DISABLE_OPT
static void artifacts_ct02_exact_two_m00_eqFunction_107(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,107};
  modelica_boolean tmp55;
  modelica_boolean tmp56;
  static const MMC_DEFSTRINGLIT(tmp57,172,"Variable violating min/max constraint: Modelica.Blocks.Types.Init.NoInit <= preparation0.stock.Integrator1.initType <= Modelica.Blocks.Types.Init.InitialOutput, has value: ");
  modelica_string tmp58;
  modelica_metatype tmpMeta59;
  static int tmp60 = 0;
  if(!tmp60)
  {
    tmp55 = GreaterEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[3]] /* preparation0.stock.Integrator1.initType PARAM */),1);
    tmp56 = LessEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[3]] /* preparation0.stock.Integrator1.initType PARAM */),4);
    if(!(tmp55 && tmp56))
    {
      tmp58 = modelica_integer_to_modelica_string_format((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[3]] /* preparation0.stock.Integrator1.initType PARAM */), (modelica_string) mmc_strings_len1[100]);
      tmpMeta59 = stringAppend(MMC_REFSTRINGLIT(tmp57),tmp58);
      {
        const char* assert_cond = "(preparation0.stock.Integrator1.initType >= Modelica.Blocks.Types.Init.NoInit and preparation0.stock.Integrator1.initType <= Modelica.Blocks.Types.Init.InitialOutput)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/thirdparty/msl/Modelica/Blocks/Continuous.mo",19,5,21,40,1};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta59));
        } else {
          FILE_INFO info = {"/thirdparty/msl/Modelica/Blocks/Continuous.mo",19,5,21,40,1};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta59));
        }
      }
      tmp60 = 1;
    }
  }
  threadData->lastEquationSolved = 107;
}

/*
equation index: 108
type: ALGORITHM

  assert(probe >= 1 and probe <= 4, "Variable violating min/max constraint: 1 <= probe <= 4, has value: " + String(probe, "d"));
*/
OMC_DISABLE_OPT
static void artifacts_ct02_exact_two_m00_eqFunction_108(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,108};
  modelica_boolean tmp61;
  modelica_boolean tmp62;
  static const MMC_DEFSTRINGLIT(tmp63,67,"Variable violating min/max constraint: 1 <= probe <= 4, has value: ");
  modelica_string tmp64;
  modelica_metatype tmpMeta65;
  static int tmp66 = 0;
  if(!tmp66)
  {
    tmp61 = GreaterEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[4]] /* probe PARAM */),((modelica_integer) 1));
    tmp62 = LessEq((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[4]] /* probe PARAM */),((modelica_integer) 4));
    if(!(tmp61 && tmp62))
    {
      tmp64 = modelica_integer_to_modelica_string_format((data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[4]] /* probe PARAM */), (modelica_string) mmc_strings_len1[100]);
      tmpMeta65 = stringAppend(MMC_REFSTRINGLIT(tmp63),tmp64);
      {
        const char* assert_cond = "(probe >= 1 and probe <= 4)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/repo/artifacts/ct02-exact-two/M/native.mo",4,5,4,43,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta65));
        } else {
          FILE_INFO info = {"/repo/artifacts/ct02-exact-two/M/native.mo",4,5,4,43,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta65));
        }
      }
      tmp66 = 1;
    }
  }
  threadData->lastEquationSolved = 108;
}
OMC_DISABLE_OPT
void artifacts_ct02_exact_two_m00_updateBoundParameters_0(DATA *data, threadData_t *threadData)
{
  static void (*const eqFunctions[31])(DATA*, threadData_t*) = {
    artifacts_ct02_exact_two_m00_eqFunction_65,
    artifacts_ct02_exact_two_m00_eqFunction_66,
    artifacts_ct02_exact_two_m00_eqFunction_70,
    artifacts_ct02_exact_two_m00_eqFunction_73,
    artifacts_ct02_exact_two_m00_eqFunction_74,
    artifacts_ct02_exact_two_m00_eqFunction_75,
    artifacts_ct02_exact_two_m00_eqFunction_76,
    artifacts_ct02_exact_two_m00_eqFunction_80,
    artifacts_ct02_exact_two_m00_eqFunction_83,
    artifacts_ct02_exact_two_m00_eqFunction_84,
    artifacts_ct02_exact_two_m00_eqFunction_85,
    artifacts_ct02_exact_two_m00_eqFunction_86,
    artifacts_ct02_exact_two_m00_eqFunction_7,
    artifacts_ct02_exact_two_m00_eqFunction_6,
    artifacts_ct02_exact_two_m00_eqFunction_5,
    artifacts_ct02_exact_two_m00_eqFunction_4,
    artifacts_ct02_exact_two_m00_eqFunction_3,
    artifacts_ct02_exact_two_m00_eqFunction_2,
    artifacts_ct02_exact_two_m00_eqFunction_1,
    artifacts_ct02_exact_two_m00_eqFunction_97,
    artifacts_ct02_exact_two_m00_eqFunction_98,
    artifacts_ct02_exact_two_m00_eqFunction_99,
    artifacts_ct02_exact_two_m00_eqFunction_100,
    artifacts_ct02_exact_two_m00_eqFunction_101,
    artifacts_ct02_exact_two_m00_eqFunction_102,
    artifacts_ct02_exact_two_m00_eqFunction_103,
    artifacts_ct02_exact_two_m00_eqFunction_104,
    artifacts_ct02_exact_two_m00_eqFunction_105,
    artifacts_ct02_exact_two_m00_eqFunction_106,
    artifacts_ct02_exact_two_m00_eqFunction_107,
    artifacts_ct02_exact_two_m00_eqFunction_108
  };
  
  for (int id = 0; id < 31; id++) {
    eqFunctions[id](data, threadData);
  }
}
OMC_DISABLE_OPT
int artifacts_ct02_exact_two_m00_updateBoundParameters(DATA *data, threadData_t *threadData)
{
  (data->simulationInfo->booleanParameter[data->simulationInfo->booleanParamsIndex[0]] /* dispatch0.release.Limiter1.strict PARAM */) = 0 /* false */;
  data->modelData->booleanParameterData[0].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[data->simulationInfo->booleanParamsIndex[1]] /* dispatch0.stock.Integrator1.use_reset PARAM */) = 0 /* false */;
  data->modelData->booleanParameterData[1].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[data->simulationInfo->booleanParamsIndex[2]] /* dispatch0.stock.Integrator1.use_set PARAM */) = 0 /* false */;
  data->modelData->booleanParameterData[2].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[data->simulationInfo->booleanParamsIndex[3]] /* preparation0.release.Limiter1.strict PARAM */) = 0 /* false */;
  data->modelData->booleanParameterData[3].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[data->simulationInfo->booleanParamsIndex[4]] /* preparation0.stock.Integrator1.use_reset PARAM */) = 0 /* false */;
  data->modelData->booleanParameterData[4].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[data->simulationInfo->booleanParamsIndex[5]] /* preparation0.stock.Integrator1.use_set PARAM */) = 0 /* false */;
  data->modelData->booleanParameterData[5].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[data->simulationInfo->booleanParamsIndex[6]] /* receipt0.deliveries.Integrator1.use_reset PARAM */) = 0 /* false */;
  data->modelData->booleanParameterData[6].time_unvarying = 1;
  (data->simulationInfo->booleanParameter[data->simulationInfo->booleanParamsIndex[7]] /* receipt0.deliveries.Integrator1.use_set PARAM */) = 0 /* false */;
  data->modelData->booleanParameterData[7].time_unvarying = 1;
  (data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[0]] /* dispatch0.release.Limiter1.homotopyType PARAM */) = 2;
  data->modelData->integerParameterData[0].time_unvarying = 1;
  (data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[1]] /* dispatch0.stock.Integrator1.initType PARAM */) = 3;
  data->modelData->integerParameterData[1].time_unvarying = 1;
  (data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[2]] /* preparation0.release.Limiter1.homotopyType PARAM */) = 2;
  data->modelData->integerParameterData[2].time_unvarying = 1;
  (data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[3]] /* preparation0.stock.Integrator1.initType PARAM */) = 3;
  data->modelData->integerParameterData[3].time_unvarying = 1;
  (data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[5]] /* receipt0.deliveries.Integrator1.initType PARAM */) = 3;
  data->modelData->integerParameterData[5].time_unvarying = 1;
  (data->simulationInfo->integerParameter[data->simulationInfo->integerParamsIndex[6]] /* report0.reportFilter.initType PARAM */) = 4;
  data->modelData->integerParameterData[6].time_unvarying = 1;
  artifacts_ct02_exact_two_m00_updateBoundParameters_0(data, threadData);
  return 0;
}

#if defined(__cplusplus)
}
#endif
