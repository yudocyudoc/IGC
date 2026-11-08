/* Main Simulation File */

#if defined(__cplusplus)
extern "C" {
#endif

#include "artifacts/ct02-exact-two/d00_model.h"
#include "simulation/solver/events.h"
#include "util/real_array.h"

/* FIXME these defines are ugly and hard to read, why not use direct function pointers instead? */
#define prefixedName_performSimulation artifacts_ct02_exact_two_d00_performSimulation
#define prefixedName_updateContinuousSystem artifacts_ct02_exact_two_d00_updateContinuousSystem
#include <simulation/solver/perform_simulation.c.inc>

#define prefixedName_performQSSSimulation artifacts_ct02_exact_two_d00_performQSSSimulation
#include <simulation/solver/perform_qss_simulation.c.inc>


/* dummy VARINFO and FILEINFO */
const VAR_INFO dummyVAR_INFO = omc_dummyVarInfo;

int artifacts_ct02_exact_two_d00_input_function(DATA *data, threadData_t *threadData)
{
  
  return 0;
}

int artifacts_ct02_exact_two_d00_input_function_init(DATA *data, threadData_t *threadData)
{
  
  return 0;
}

int artifacts_ct02_exact_two_d00_input_function_updateStartValues(DATA *data, threadData_t *threadData)
{
  
  return 0;
}

int artifacts_ct02_exact_two_d00_inputNames(DATA *data, char ** names){
  
  return 0;
}

int artifacts_ct02_exact_two_d00_data_function(DATA *data, threadData_t *threadData)
{
  return 0;
}

int artifacts_ct02_exact_two_d00_dataReconciliationInputNames(DATA *data, char ** names){
  
  return 0;
}

int artifacts_ct02_exact_two_d00_dataReconciliationUnmeasuredVariables(DATA *data, char ** names)
{
  
  return 0;
}

int artifacts_ct02_exact_two_d00_output_function(DATA *data, threadData_t *threadData)
{
  
  return 0;
}

int artifacts_ct02_exact_two_d00_setc_function(DATA *data, threadData_t *threadData)
{
  
  return 0;
}

int artifacts_ct02_exact_two_d00_setb_function(DATA *data, threadData_t *threadData)
{
  
  return 0;
}


/*
equation index: 10
type: SIMPLE_ASSIGN
$cse1 = max(0.0, s1 / responseTime)
*/
void artifacts_ct02_exact_two_d00_eqFunction_10(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,10};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[6]] /* $cse1 variable */) = fmax(0.0,DIVISION_SIM((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[2]] /* s1 STATE(1) */),(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[4]] /* responseTime PARAM */),"responseTime",equationIndexes));
  threadData->lastEquationSolved = 10;
}

/*
equation index: 11
type: SIMPLE_ASSIGN
f1 = min(capacity, $cse1)
*/
void artifacts_ct02_exact_two_d00_eqFunction_11(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,11};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[7]] /* f1 variable */) = fmin((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[0]] /* capacity PARAM */),(data->localData[0]->realVars[data->simulationInfo->realVarsIndex[6]] /* $cse1 variable */));
  threadData->lastEquationSolved = 11;
}

/*
equation index: 12
type: SIMPLE_ASSIGN
inputRate = if time < pulseDuration then pulseRate else 0.0
*/
void artifacts_ct02_exact_two_d00_eqFunction_12(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,12};
  modelica_boolean tmp0;
  modelica_real tmp1;
  modelica_real tmp2;
  tmp1 = 1.0;
  tmp2 = fabs((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[2]] /* pulseDuration PARAM */));
  relationhysteresis(data, &tmp0, data->localData[0]->timeValue, (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[2]] /* pulseDuration PARAM */), tmp1, tmp2, 0, Less, LessZC);
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[8]] /* inputRate variable */) = (tmp0?(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[3]] /* pulseRate PARAM */):0.0);
  threadData->lastEquationSolved = 12;
}

/*
equation index: 13
type: SIMPLE_ASSIGN
$DER.s1 = inputRate - f1
*/
void artifacts_ct02_exact_two_d00_eqFunction_13(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,13};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[5]] /* der(s1) STATE_DER */) = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[8]] /* inputRate variable */) - (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[7]] /* f1 variable */);
  threadData->lastEquationSolved = 13;
}

/*
equation index: 14
type: SIMPLE_ASSIGN
$DER.delivered = f1
*/
void artifacts_ct02_exact_two_d00_eqFunction_14(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,14};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[3]] /* der(delivered) STATE_DER */) = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[7]] /* f1 variable */);
  threadData->lastEquationSolved = 14;
}

/*
equation index: 15
type: SIMPLE_ASSIGN
$DER.lost = 0.0
*/
void artifacts_ct02_exact_two_d00_eqFunction_15(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,15};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[4]] /* der(lost) STATE_DER */) = 0.0;
  threadData->lastEquationSolved = 15;
}

OMC_DISABLE_OPT
int artifacts_ct02_exact_two_d00_functionDAE(DATA *data, threadData_t *threadData)
{
  int equationIndexes[1] = {0};
#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_tick(SIM_TIMER_DAE);
#endif

  data->simulationInfo->needToIterate = 0;
  data->simulationInfo->discreteCall = 1;
  artifacts_ct02_exact_two_d00_functionLocalKnownVars(data, threadData);
  static void (*const eqFunctions[6])(DATA*, threadData_t*) = {
    artifacts_ct02_exact_two_d00_eqFunction_10,
    artifacts_ct02_exact_two_d00_eqFunction_11,
    artifacts_ct02_exact_two_d00_eqFunction_12,
    artifacts_ct02_exact_two_d00_eqFunction_13,
    artifacts_ct02_exact_two_d00_eqFunction_14,
    artifacts_ct02_exact_two_d00_eqFunction_15
  };
  
  for (int id = 0; id < 6; id++) {
    eqFunctions[id](data, threadData);
  }
  data->simulationInfo->discreteCall = 0;
  
#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_accumulate(SIM_TIMER_DAE);
#endif
  return 0;
}


int artifacts_ct02_exact_two_d00_functionLocalKnownVars(DATA *data, threadData_t *threadData)
{
  
  return 0;
}

/* forwarded equations */
extern void artifacts_ct02_exact_two_d00_eqFunction_10(DATA* data, threadData_t *threadData);
extern void artifacts_ct02_exact_two_d00_eqFunction_11(DATA* data, threadData_t *threadData);
extern void artifacts_ct02_exact_two_d00_eqFunction_12(DATA* data, threadData_t *threadData);
extern void artifacts_ct02_exact_two_d00_eqFunction_13(DATA* data, threadData_t *threadData);
extern void artifacts_ct02_exact_two_d00_eqFunction_14(DATA* data, threadData_t *threadData);
extern void artifacts_ct02_exact_two_d00_eqFunction_15(DATA* data, threadData_t *threadData);

static void functionODE_system0(DATA *data, threadData_t *threadData)
{
  static void (*const eqFunctions[6])(DATA*, threadData_t*) = {
    artifacts_ct02_exact_two_d00_eqFunction_10,
    artifacts_ct02_exact_two_d00_eqFunction_11,
    artifacts_ct02_exact_two_d00_eqFunction_12,
    artifacts_ct02_exact_two_d00_eqFunction_13,
    artifacts_ct02_exact_two_d00_eqFunction_14,
    artifacts_ct02_exact_two_d00_eqFunction_15
  };
  
  for (int id = 0; id < 6; id++) {
    eqFunctions[id](data, threadData);
  }
}

int artifacts_ct02_exact_two_d00_functionODE(DATA *data, threadData_t *threadData)
{
#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_tick(SIM_TIMER_FUNCTION_ODE);
#endif

  
  data->simulationInfo->callStatistics.functionODE++;
  
  artifacts_ct02_exact_two_d00_functionLocalKnownVars(data, threadData);
  functionODE_system0(data, threadData);

#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_accumulate(SIM_TIMER_FUNCTION_ODE);
#endif

  return 0;
}

/* forward the main in the simulation runtime */
extern int _main_SimulationRuntime(int argc, char **argv, DATA *data, threadData_t *threadData);
extern int _main_OptimizationRuntime(int argc, char **argv, DATA *data, threadData_t *threadData);

#include "artifacts/ct02-exact-two/d00_12jac.h"
#include "artifacts/ct02-exact-two/d00_13opt.h"

struct OpenModelicaGeneratedFunctionCallbacks artifacts_ct02_exact_two_d00_callback = {
  (int (*)(DATA *, threadData_t *, void *)) artifacts_ct02_exact_two_d00_performSimulation,    /* performSimulation */
  (int (*)(DATA *, threadData_t *, void *)) artifacts_ct02_exact_two_d00_performQSSSimulation,    /* performQSSSimulation */
  artifacts_ct02_exact_two_d00_updateContinuousSystem,    /* updateContinuousSystem */
  artifacts_ct02_exact_two_d00_callExternalObjectDestructors,    /* callExternalObjectDestructors */
  NULL,    /* initialNonLinearSystem */
  NULL,    /* initialLinearSystem */
  NULL,    /* initialMixedSystem */
  #if !defined(OMC_NO_STATESELECTION)
  artifacts_ct02_exact_two_d00_initializeStateSets,
  #else
  NULL,
  #endif    /* initializeStateSets */
  artifacts_ct02_exact_two_d00_initializeDAEmodeData,
  artifacts_ct02_exact_two_d00_functionODE,
  artifacts_ct02_exact_two_d00_functionAlgebraics,
  artifacts_ct02_exact_two_d00_functionDAE,
  artifacts_ct02_exact_two_d00_functionLocalKnownVars,
  artifacts_ct02_exact_two_d00_input_function,
  artifacts_ct02_exact_two_d00_input_function_init,
  artifacts_ct02_exact_two_d00_input_function_updateStartValues,
  artifacts_ct02_exact_two_d00_data_function,
  artifacts_ct02_exact_two_d00_output_function,
  artifacts_ct02_exact_two_d00_setc_function,
  artifacts_ct02_exact_two_d00_setb_function,
  artifacts_ct02_exact_two_d00_function_storeDelayed,
  artifacts_ct02_exact_two_d00_function_storeSpatialDistribution,
  artifacts_ct02_exact_two_d00_function_initSpatialDistribution,
  artifacts_ct02_exact_two_d00_updateBoundVariableAttributes,
  artifacts_ct02_exact_two_d00_functionInitialEquations,
  GLOBAL_EQUIDISTANT_HOMOTOPY,
  NULL,
  artifacts_ct02_exact_two_d00_functionRemovedInitialEquations,
  artifacts_ct02_exact_two_d00_updateBoundParameters,
  artifacts_ct02_exact_two_d00_checkForAsserts,
  artifacts_ct02_exact_two_d00_function_ZeroCrossingsEquations,
  artifacts_ct02_exact_two_d00_function_ZeroCrossings,
  artifacts_ct02_exact_two_d00_function_updateRelations,
  artifacts_ct02_exact_two_d00_zeroCrossingDescription,
  artifacts_ct02_exact_two_d00_relationDescription,
  artifacts_ct02_exact_two_d00_function_initSample,
  artifacts_ct02_exact_two_d00_INDEX_JAC_A,
  artifacts_ct02_exact_two_d00_INDEX_JAC_B,
  artifacts_ct02_exact_two_d00_INDEX_JAC_C,
  artifacts_ct02_exact_two_d00_INDEX_JAC_D,
  artifacts_ct02_exact_two_d00_INDEX_JAC_F,
  artifacts_ct02_exact_two_d00_INDEX_JAC_H,
  artifacts_ct02_exact_two_d00_initialAnalyticJacobianA,
  artifacts_ct02_exact_two_d00_initialAnalyticJacobianB,
  artifacts_ct02_exact_two_d00_initialAnalyticJacobianC,
  artifacts_ct02_exact_two_d00_initialAnalyticJacobianD,
  artifacts_ct02_exact_two_d00_initialAnalyticJacobianF,
  artifacts_ct02_exact_two_d00_initialAnalyticJacobianH,
  artifacts_ct02_exact_two_d00_functionJacA_column,
  artifacts_ct02_exact_two_d00_functionJacB_column,
  artifacts_ct02_exact_two_d00_functionJacC_column,
  artifacts_ct02_exact_two_d00_functionJacD_column,
  artifacts_ct02_exact_two_d00_functionJacF_column,
  artifacts_ct02_exact_two_d00_functionJacH_column,
  artifacts_ct02_exact_two_d00_linear_model_frame,
  artifacts_ct02_exact_two_d00_linear_model_datarecovery_frame,
  artifacts_ct02_exact_two_d00_mayer,
  artifacts_ct02_exact_two_d00_lagrange,
  artifacts_ct02_exact_two_d00_getInputVarIndicesInOptimization,
  artifacts_ct02_exact_two_d00_pickUpBoundsForInputsInOptimization,
  artifacts_ct02_exact_two_d00_setInputData,
  artifacts_ct02_exact_two_d00_getTimeGrid,
  artifacts_ct02_exact_two_d00_symbolicInlineSystem,
  artifacts_ct02_exact_two_d00_function_initSynchronous,
  artifacts_ct02_exact_two_d00_function_updateSynchronous,
  artifacts_ct02_exact_two_d00_function_equationsSynchronous,
  artifacts_ct02_exact_two_d00_inputNames,
  artifacts_ct02_exact_two_d00_dataReconciliationInputNames,
  artifacts_ct02_exact_two_d00_dataReconciliationUnmeasuredVariables,
  NULL,
  NULL,
  NULL,
  NULL,
  -1,
  NULL,
  NULL,
  -1

};

#define _OMC_LIT_RESOURCE_0_name_data "DStockFlow_5f8781847cb6"
#define _OMC_LIT_RESOURCE_0_dir_data "/repo/artifacts/ct02-exact-two/D"
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_0_name,23,_OMC_LIT_RESOURCE_0_name_data);
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_0_dir,32,_OMC_LIT_RESOURCE_0_dir_data);

static const MMC_DEFSTRUCTLIT(_OMC_LIT_RESOURCES,2,MMC_ARRAY_TAG) {MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_0_name), MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_0_dir)}};
void artifacts_ct02_exact_two_d00_setupDataStruc(DATA *data, threadData_t *threadData)
{
  assertStreamPrint(threadData,0!=data, "Error while initialize Data");
  threadData->localRoots[LOCAL_ROOT_SIMULATION_DATA] = data;
  data->callback = &artifacts_ct02_exact_two_d00_callback;
  OpenModelica_updateUriMapping(threadData, MMC_REFSTRUCTLIT(_OMC_LIT_RESOURCES));
  data->modelData->modelName = "DStockFlow_5f8781847cb6";
  data->modelData->modelFilePrefix = "artifacts/ct02-exact-two/d00";
  data->modelData->modelFileName = "DStockFlow_5f8781847cb6.mo";
  data->modelData->resultFileName = NULL;
  data->modelData->modelDir = "/repo/artifacts/ct02-exact-two/D";
  data->modelData->modelGUID = "{d83eb256-4ab7-43ff-b3ad-e91c7ab97db6}";
  #if defined(OPENMODELICA_XML_FROM_FILE_AT_RUNTIME)
  data->modelData->initXMLData = NULL;
  data->modelData->modelDataXml.infoXMLData = NULL;
  #else
  #if defined(_MSC_VER) /* handle joke compilers */
  {
  /* for MSVC we encode a string like char x[] = {'a', 'b', 'c', '\0'} */
  /* because the string constant limit is 65535 bytes */
  static const char contents_init[] =
    #include "artifacts/ct02-exact-two/d00_init.c"
    ;
  static const char contents_info[] =
    #include "artifacts/ct02-exact-two/d00_info.c"
    ;
    data->modelData->initXMLData = contents_init;
    data->modelData->modelDataXml.infoXMLData = contents_info;
  }
  #else /* handle real compilers */
  data->modelData->initXMLData =
  #include "artifacts/ct02-exact-two/d00_init.c"
    ;
  data->modelData->modelDataXml.infoXMLData =
  #include "artifacts/ct02-exact-two/d00_info.c"
    ;
  #endif /* defined(_MSC_VER) */
  #endif /* defined(OPENMODELICA_XML_FROM_FILE_AT_RUNTIME) */
  data->modelData->modelDataXml.fileName = "artifacts/ct02-exact-two/d00_info.json";
  data->modelData->resourcesDir = NULL;
  data->modelData->runTestsuite = 0;
  data->modelData->nStatesArray = 3;
  data->modelData->nDiscreteReal = 0;
  data->modelData->nVariablesRealArray = 10;
  data->modelData->nVariablesIntegerArray = 0;
  data->modelData->nVariablesBooleanArray = 0;
  data->modelData->nVariablesStringArray = 0;
  data->modelData->nParametersRealArray = 5;
  data->modelData->nParametersIntegerArray = 0;
  data->modelData->nParametersBooleanArray = 0;
  data->modelData->nParametersStringArray = 0;
  data->modelData->nParametersReal = 5;
  data->modelData->nParametersInteger = 0;
  data->modelData->nParametersBoolean = 0;
  data->modelData->nParametersString = 0;
  data->modelData->nAliasRealArray = 0;
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
  data->modelData->modelDataXml.nEquations = 17;
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
  
    artifacts_ct02_exact_two_d00_setupDataStruc(&data, threadData);
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


