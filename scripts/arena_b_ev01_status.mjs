/**
 * EV-01-specific receipt adjudication. Pure function: no provider or solver calls.
 * Critically, no native model means that an absent horizon is NOT a bad horizon.
 * Original historical B runner is never modified or imported here.
 */
export function classifyEv01NativeResult(r) {
  if (r?.case_id !== 'EV-01') throw new Error('EV01_RECEIPT_CASE_REQUIRED');
  const attempted = Number(r?.provider_calls ?? 0);
  const native = r?.model_returned === true;
  const bridge = String(r?.bridge_error ?? '');
  const hasHttpReply = Number.isInteger(r?.http_status) && r.http_status >= 100;
  const providerResponseSaved = r?.raw_provider_saved === true;
  const common = {
    provider_calls_attempted: attempted,
    provider_response_observed: hasHttpReply,
    raw_provider_response_observed: providerResponseSaved,
    provider_billing: r?.provider_usage ? 'PROVIDER_USAGE_RECEIVED' : 'UNKNOWN',
    native_model_available: native,
  };
  if (!native && r.runner_error && attempted === 0) {
    return {...common,status:'EV01_RUNNER_FAILURE_BEFORE_PROVIDER_CALL',
      G0:'NOT_REACHED_NO_NATIVE_MODEL',reason:'RUNNER_PRECONDITION_OR_EXECUTION_FAILED'};
  }
  if (!native) {
    if (attempted > 0 && /aborted.*timeout|timeout|timed out/i.test(bridge)) {
      return {...common, status:'EV01_PROVIDER_TRANSPORT_TIMEOUT_NO_NATIVE_MODEL',
        G0:'NOT_REACHED_NO_NATIVE_MODEL', reason:'PROVIDER_TIMEOUT_BEFORE_HTTP_RESPONSE'};
    }
    if (attempted > 0 && bridge) {
      return {...common,status:'EV01_TRANSPORT_ERROR_NO_NATIVE_MODEL',
        G0:'NOT_REACHED_NO_NATIVE_MODEL',reason:'BRIDGE_FAILED'};
    }
    return {...common,status:attempted ? 'EV01_NATIVE_GENERATION_FAILED_NO_MODEL'
                                   : 'EV01_NO_PROVIDER_CALL_OR_NATIVE_MODEL',
      G0:'NOT_REACHED_NO_NATIVE_MODEL',reason:'NATIVE_MODEL_UNAVAILABLE'};
  }
  if (r.horizon_matches_case !== true) {
    return {...common,status:'EV01_NATIVE_HORIZON_NOT_COMPARABLE',
      G0:'UNASSESSED_NATIVE_HORIZON_MISMATCH',reason:'NATIVE_RETURNED_HORIZON_INVALID'};
  }
  return {...common,status:r.mode==='mock' ? 'ORIGINAL_ENGINE_OFFLINE_PATH_PASS'
                                            : 'ORIGINAL_ENGINE_LIVE_OUTPUT_RETURNED',
    G0:'NATIVE_GENERATION_ONLY_TRANSLATION_PENDING',reason:'NATIVE_RETURNED'};
}