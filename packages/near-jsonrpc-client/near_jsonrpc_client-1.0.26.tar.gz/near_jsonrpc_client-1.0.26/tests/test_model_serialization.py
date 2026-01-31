import json
from pathlib import Path
import pytest
import near_jsonrpc_models


# ----------------------------------------------------------------------
# Generated model (de)serialization tests
# ----------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "json"

def load_mock_json(filename: str) -> str:
    path = FIXTURES_DIR / filename
    if not path.exists():
        pytest.fail(f'Mock file {filename} does not exist!')
    return path.read_text(encoding='utf-8')


def test_access_key_encode_decode():
    data = load_mock_json('access_key.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'AccessKey')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for AccessKey')


def test_access_key_creation_config_view_encode_decode():
    data = load_mock_json('access_key_creation_config_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'AccessKeyCreationConfigView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for AccessKeyCreationConfigView')


def test_access_key_info_view_encode_decode():
    data = load_mock_json('access_key_info_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'AccessKeyInfoView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for AccessKeyInfoView')


def test_access_key_list_encode_decode():
    data = load_mock_json('access_key_list.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'AccessKeyList')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for AccessKeyList')


def test_access_key_permission_encode_decode():
    data = load_mock_json('access_key_permission.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'AccessKeyPermission')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for AccessKeyPermission')


def test_access_key_permission_view_encode_decode():
    data = load_mock_json('access_key_permission_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'AccessKeyPermissionView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for AccessKeyPermissionView')


def test_access_key_view_encode_decode():
    data = load_mock_json('access_key_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'AccessKeyView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for AccessKeyView')


def test_account_creation_config_view_encode_decode():
    data = load_mock_json('account_creation_config_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'AccountCreationConfigView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for AccountCreationConfigView')


def test_account_data_view_encode_decode():
    data = load_mock_json('account_data_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'AccountDataView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for AccountDataView')


def test_account_id_encode_decode():
    data = load_mock_json('account_id.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'AccountId')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for AccountId')


def test_account_id_validity_rules_version_encode_decode():
    data = load_mock_json('account_id_validity_rules_version.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'AccountIdValidityRulesVersion')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for AccountIdValidityRulesVersion')


def test_account_info_encode_decode():
    data = load_mock_json('account_info.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'AccountInfo')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for AccountInfo')


def test_account_view_encode_decode():
    data = load_mock_json('account_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'AccountView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for AccountView')


def test_account_with_public_key_encode_decode():
    data = load_mock_json('account_with_public_key.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'AccountWithPublicKey')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for AccountWithPublicKey')


def test_action_creation_config_view_encode_decode():
    data = load_mock_json('action_creation_config_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ActionCreationConfigView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ActionCreationConfigView')


def test_action_error_encode_decode():
    data = load_mock_json('action_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ActionError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ActionError')


def test_action_error_kind_encode_decode():
    data = load_mock_json('action_error_kind.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ActionErrorKind')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ActionErrorKind')


def test_action_view_encode_decode():
    data = load_mock_json('action_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ActionView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ActionView')


def test_actions_validation_error_encode_decode():
    data = load_mock_json('actions_validation_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ActionsValidationError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ActionsValidationError')


def test_add_key_action_encode_decode():
    data = load_mock_json('add_key_action.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'AddKeyAction')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for AddKeyAction')


def test_bandwidth_request_encode_decode():
    data = load_mock_json('bandwidth_request.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'BandwidthRequest')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for BandwidthRequest')


def test_bandwidth_request_bitmap_encode_decode():
    data = load_mock_json('bandwidth_request_bitmap.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'BandwidthRequestBitmap')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for BandwidthRequestBitmap')


def test_bandwidth_requests_encode_decode():
    data = load_mock_json('bandwidth_requests.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'BandwidthRequests')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for BandwidthRequests')


def test_bandwidth_requests_v1_encode_decode():
    data = load_mock_json('bandwidth_requests_v1.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'BandwidthRequestsV1')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for BandwidthRequestsV1')


def test_block_header_inner_lite_view_encode_decode():
    data = load_mock_json('block_header_inner_lite_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'BlockHeaderInnerLiteView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for BlockHeaderInnerLiteView')


def test_block_header_view_encode_decode():
    data = load_mock_json('block_header_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'BlockHeaderView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for BlockHeaderView')


def test_block_id_encode_decode():
    data = load_mock_json('block_id.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'BlockId')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for BlockId')


def test_block_reference_encode_decode():
    data = load_mock_json('block_reference.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'BlockReference')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for BlockReference')


def test_block_status_view_encode_decode():
    data = load_mock_json('block_status_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'BlockStatusView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for BlockStatusView')


def test_call_result_encode_decode():
    data = load_mock_json('call_result.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'CallResult')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for CallResult')


def test_catchup_status_view_encode_decode():
    data = load_mock_json('catchup_status_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'CatchupStatusView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for CatchupStatusView')


def test_chunk_distribution_network_config_encode_decode():
    data = load_mock_json('chunk_distribution_network_config.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ChunkDistributionNetworkConfig')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ChunkDistributionNetworkConfig')


def test_chunk_distribution_uris_encode_decode():
    data = load_mock_json('chunk_distribution_uris.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ChunkDistributionUris')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ChunkDistributionUris')


def test_chunk_hash_encode_decode():
    data = load_mock_json('chunk_hash.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ChunkHash')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ChunkHash')


def test_chunk_header_view_encode_decode():
    data = load_mock_json('chunk_header_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ChunkHeaderView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ChunkHeaderView')


def test_cloud_archival_writer_config_encode_decode():
    data = load_mock_json('cloud_archival_writer_config.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'CloudArchivalWriterConfig')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for CloudArchivalWriterConfig')


def test_compilation_error_encode_decode():
    data = load_mock_json('compilation_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'CompilationError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for CompilationError')


def test_congestion_control_config_view_encode_decode():
    data = load_mock_json('congestion_control_config_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'CongestionControlConfigView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for CongestionControlConfigView')


def test_congestion_info_view_encode_decode():
    data = load_mock_json('congestion_info_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'CongestionInfoView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for CongestionInfoView')


def test_contract_code_view_encode_decode():
    data = load_mock_json('contract_code_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ContractCodeView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ContractCodeView')


def test_cost_gas_used_encode_decode():
    data = load_mock_json('cost_gas_used.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'CostGasUsed')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for CostGasUsed')


def test_create_account_action_encode_decode():
    data = load_mock_json('create_account_action.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'CreateAccountAction')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for CreateAccountAction')


def test_crypto_hash_encode_decode():
    data = load_mock_json('crypto_hash.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'CryptoHash')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for CryptoHash')


def test_current_epoch_validator_info_encode_decode():
    data = load_mock_json('current_epoch_validator_info.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'CurrentEpochValidatorInfo')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for CurrentEpochValidatorInfo')


def test_data_receipt_creation_config_view_encode_decode():
    data = load_mock_json('data_receipt_creation_config_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'DataReceiptCreationConfigView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for DataReceiptCreationConfigView')


def test_data_receiver_view_encode_decode():
    data = load_mock_json('data_receiver_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'DataReceiverView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for DataReceiverView')


def test_delegate_action_encode_decode():
    data = load_mock_json('delegate_action.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'DelegateAction')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for DelegateAction')


def test_delete_account_action_encode_decode():
    data = load_mock_json('delete_account_action.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'DeleteAccountAction')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for DeleteAccountAction')


def test_delete_key_action_encode_decode():
    data = load_mock_json('delete_key_action.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'DeleteKeyAction')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for DeleteKeyAction')


def test_deploy_contract_action_encode_decode():
    data = load_mock_json('deploy_contract_action.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'DeployContractAction')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for DeployContractAction')


def test_deploy_global_contract_action_encode_decode():
    data = load_mock_json('deploy_global_contract_action.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'DeployGlobalContractAction')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for DeployGlobalContractAction')


def test_detailed_debug_status_encode_decode():
    data = load_mock_json('detailed_debug_status.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'DetailedDebugStatus')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for DetailedDebugStatus')


def test_deterministic_account_state_init_encode_decode():
    data = load_mock_json('deterministic_account_state_init.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'DeterministicAccountStateInit')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for DeterministicAccountStateInit')


def test_deterministic_account_state_init_v1_encode_decode():
    data = load_mock_json('deterministic_account_state_init_v1.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'DeterministicAccountStateInitV1')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for DeterministicAccountStateInitV1')


def test_deterministic_state_init_action_encode_decode():
    data = load_mock_json('deterministic_state_init_action.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'DeterministicStateInitAction')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for DeterministicStateInitAction')


def test_direction_encode_decode():
    data = load_mock_json('direction.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'Direction')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for Direction')


def test_dump_config_encode_decode():
    data = load_mock_json('dump_config.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'DumpConfig')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for DumpConfig')


def test_duration_as_std_schema_provider_encode_decode():
    data = load_mock_json('duration_as_std_schema_provider.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'DurationAsStdSchemaProvider')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for DurationAsStdSchemaProvider')


def test_epoch_id_encode_decode():
    data = load_mock_json('epoch_id.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'EpochId')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for EpochId')


def test_epoch_sync_config_encode_decode():
    data = load_mock_json('epoch_sync_config.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'EpochSyncConfig')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for EpochSyncConfig')


def test_error_wrapper_for_genesis_config_error_encode_decode():
    data = load_mock_json('error_wrapper_for_genesis_config_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ErrorWrapperForGenesisConfigError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ErrorWrapperForGenesisConfigError')


def test_error_wrapper_for_rpc_block_error_encode_decode():
    data = load_mock_json('error_wrapper_for_rpc_block_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ErrorWrapperForRpcBlockError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ErrorWrapperForRpcBlockError')


def test_error_wrapper_for_rpc_call_function_error_encode_decode():
    data = load_mock_json('error_wrapper_for_rpc_call_function_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ErrorWrapperForRpcCallFunctionError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ErrorWrapperForRpcCallFunctionError')


def test_error_wrapper_for_rpc_chunk_error_encode_decode():
    data = load_mock_json('error_wrapper_for_rpc_chunk_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ErrorWrapperForRpcChunkError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ErrorWrapperForRpcChunkError')


def test_error_wrapper_for_rpc_client_config_error_encode_decode():
    data = load_mock_json('error_wrapper_for_rpc_client_config_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ErrorWrapperForRpcClientConfigError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ErrorWrapperForRpcClientConfigError')


def test_error_wrapper_for_rpc_gas_price_error_encode_decode():
    data = load_mock_json('error_wrapper_for_rpc_gas_price_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ErrorWrapperForRpcGasPriceError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ErrorWrapperForRpcGasPriceError')


def test_error_wrapper_for_rpc_light_client_next_block_error_encode_decode():
    data = load_mock_json('error_wrapper_for_rpc_light_client_next_block_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ErrorWrapperForRpcLightClientNextBlockError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ErrorWrapperForRpcLightClientNextBlockError')


def test_error_wrapper_for_rpc_light_client_proof_error_encode_decode():
    data = load_mock_json('error_wrapper_for_rpc_light_client_proof_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ErrorWrapperForRpcLightClientProofError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ErrorWrapperForRpcLightClientProofError')


def test_error_wrapper_for_rpc_maintenance_windows_error_encode_decode():
    data = load_mock_json('error_wrapper_for_rpc_maintenance_windows_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ErrorWrapperForRpcMaintenanceWindowsError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ErrorWrapperForRpcMaintenanceWindowsError')


def test_error_wrapper_for_rpc_network_info_error_encode_decode():
    data = load_mock_json('error_wrapper_for_rpc_network_info_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ErrorWrapperForRpcNetworkInfoError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ErrorWrapperForRpcNetworkInfoError')


def test_error_wrapper_for_rpc_protocol_config_error_encode_decode():
    data = load_mock_json('error_wrapper_for_rpc_protocol_config_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ErrorWrapperForRpcProtocolConfigError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ErrorWrapperForRpcProtocolConfigError')


def test_error_wrapper_for_rpc_query_error_encode_decode():
    data = load_mock_json('error_wrapper_for_rpc_query_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ErrorWrapperForRpcQueryError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ErrorWrapperForRpcQueryError')


def test_error_wrapper_for_rpc_receipt_error_encode_decode():
    data = load_mock_json('error_wrapper_for_rpc_receipt_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ErrorWrapperForRpcReceiptError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ErrorWrapperForRpcReceiptError')


def test_error_wrapper_for_rpc_split_storage_info_error_encode_decode():
    data = load_mock_json('error_wrapper_for_rpc_split_storage_info_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ErrorWrapperForRpcSplitStorageInfoError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ErrorWrapperForRpcSplitStorageInfoError')


def test_error_wrapper_for_rpc_state_changes_error_encode_decode():
    data = load_mock_json('error_wrapper_for_rpc_state_changes_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ErrorWrapperForRpcStateChangesError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ErrorWrapperForRpcStateChangesError')


def test_error_wrapper_for_rpc_status_error_encode_decode():
    data = load_mock_json('error_wrapper_for_rpc_status_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ErrorWrapperForRpcStatusError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ErrorWrapperForRpcStatusError')


def test_error_wrapper_for_rpc_transaction_error_encode_decode():
    data = load_mock_json('error_wrapper_for_rpc_transaction_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ErrorWrapperForRpcTransactionError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ErrorWrapperForRpcTransactionError')


def test_error_wrapper_for_rpc_validator_error_encode_decode():
    data = load_mock_json('error_wrapper_for_rpc_validator_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ErrorWrapperForRpcValidatorError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ErrorWrapperForRpcValidatorError')


def test_error_wrapper_for_rpc_view_access_key_error_encode_decode():
    data = load_mock_json('error_wrapper_for_rpc_view_access_key_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ErrorWrapperForRpcViewAccessKeyError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ErrorWrapperForRpcViewAccessKeyError')


def test_error_wrapper_for_rpc_view_access_key_list_error_encode_decode():
    data = load_mock_json('error_wrapper_for_rpc_view_access_key_list_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ErrorWrapperForRpcViewAccessKeyListError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ErrorWrapperForRpcViewAccessKeyListError')


def test_error_wrapper_for_rpc_view_account_error_encode_decode():
    data = load_mock_json('error_wrapper_for_rpc_view_account_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ErrorWrapperForRpcViewAccountError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ErrorWrapperForRpcViewAccountError')


def test_error_wrapper_for_rpc_view_code_error_encode_decode():
    data = load_mock_json('error_wrapper_for_rpc_view_code_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ErrorWrapperForRpcViewCodeError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ErrorWrapperForRpcViewCodeError')


def test_error_wrapper_for_rpc_view_state_error_encode_decode():
    data = load_mock_json('error_wrapper_for_rpc_view_state_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ErrorWrapperForRpcViewStateError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ErrorWrapperForRpcViewStateError')


def test_execution_metadata_view_encode_decode():
    data = load_mock_json('execution_metadata_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ExecutionMetadataView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ExecutionMetadataView')


def test_execution_outcome_view_encode_decode():
    data = load_mock_json('execution_outcome_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ExecutionOutcomeView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ExecutionOutcomeView')


def test_execution_outcome_with_id_view_encode_decode():
    data = load_mock_json('execution_outcome_with_id_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ExecutionOutcomeWithIdView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ExecutionOutcomeWithIdView')


def test_execution_status_view_encode_decode():
    data = load_mock_json('execution_status_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ExecutionStatusView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ExecutionStatusView')


def test_ext_costs_config_view_encode_decode():
    data = load_mock_json('ext_costs_config_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ExtCostsConfigView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ExtCostsConfigView')


def test_external_storage_config_encode_decode():
    data = load_mock_json('external_storage_config.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ExternalStorageConfig')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ExternalStorageConfig')


def test_external_storage_location_encode_decode():
    data = load_mock_json('external_storage_location.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ExternalStorageLocation')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ExternalStorageLocation')


def test_fee_encode_decode():
    data = load_mock_json('fee.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'Fee')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for Fee')


def test_final_execution_outcome_view_encode_decode():
    data = load_mock_json('final_execution_outcome_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'FinalExecutionOutcomeView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for FinalExecutionOutcomeView')


def test_final_execution_outcome_with_receipt_view_encode_decode():
    data = load_mock_json('final_execution_outcome_with_receipt_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'FinalExecutionOutcomeWithReceiptView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for FinalExecutionOutcomeWithReceiptView')


def test_final_execution_status_encode_decode():
    data = load_mock_json('final_execution_status.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'FinalExecutionStatus')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for FinalExecutionStatus')


def test_finality_encode_decode():
    data = load_mock_json('finality.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'Finality')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for Finality')


def test_function_args_encode_decode():
    data = load_mock_json('function_args.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'FunctionArgs')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for FunctionArgs')


def test_function_call_action_encode_decode():
    data = load_mock_json('function_call_action.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'FunctionCallAction')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for FunctionCallAction')


def test_function_call_error_encode_decode():
    data = load_mock_json('function_call_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'FunctionCallError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for FunctionCallError')


def test_function_call_permission_encode_decode():
    data = load_mock_json('function_call_permission.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'FunctionCallPermission')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for FunctionCallPermission')


def test_gcconfig_encode_decode():
    data = load_mock_json('gcconfig.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'GCConfig')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for GCConfig')


def test_gas_key_info_encode_decode():
    data = load_mock_json('gas_key_info.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'GasKeyInfo')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for GasKeyInfo')


def test_genesis_config_encode_decode():
    data = load_mock_json('genesis_config.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'GenesisConfig')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for GenesisConfig')


def test_genesis_config_error_encode_decode():
    data = load_mock_json('genesis_config_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'GenesisConfigError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for GenesisConfigError')


def test_genesis_config_request_encode_decode():
    data = load_mock_json('genesis_config_request.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'GenesisConfigRequest')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for GenesisConfigRequest')


def test_global_contract_deploy_mode_encode_decode():
    data = load_mock_json('global_contract_deploy_mode.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'GlobalContractDeployMode')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for GlobalContractDeployMode')


def test_global_contract_identifier_encode_decode():
    data = load_mock_json('global_contract_identifier.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'GlobalContractIdentifier')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for GlobalContractIdentifier')


def test_global_contract_identifier_view_encode_decode():
    data = load_mock_json('global_contract_identifier_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'GlobalContractIdentifierView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for GlobalContractIdentifierView')


def test_host_error_encode_decode():
    data = load_mock_json('host_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'HostError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for HostError')


def test_internal_error_encode_decode():
    data = load_mock_json('internal_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'InternalError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for InternalError')


def test_invalid_access_key_error_encode_decode():
    data = load_mock_json('invalid_access_key_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'InvalidAccessKeyError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for InvalidAccessKeyError')


def test_invalid_tx_error_encode_decode():
    data = load_mock_json('invalid_tx_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'InvalidTxError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for InvalidTxError')


def test_json_rpc_request_for_experimental_call_function_encode_decode():
    data = load_mock_json('json_rpc_request_for_experimental_call_function.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForExperimentalCallFunction')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForExperimentalCallFunction')


def test_json_rpc_request_for_experimental_changes_encode_decode():
    data = load_mock_json('json_rpc_request_for_experimental_changes.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForExperimentalChanges')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForExperimentalChanges')


def test_json_rpc_request_for_experimental_changes_in_block_encode_decode():
    data = load_mock_json('json_rpc_request_for_experimental_changes_in_block.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForExperimentalChangesInBlock')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForExperimentalChangesInBlock')


def test_json_rpc_request_for_experimental_congestion_level_encode_decode():
    data = load_mock_json('json_rpc_request_for_experimental_congestion_level.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForExperimentalCongestionLevel')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForExperimentalCongestionLevel')


def test_json_rpc_request_for_experimental_genesis_config_encode_decode():
    data = load_mock_json('json_rpc_request_for_experimental_genesis_config.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForExperimentalGenesisConfig')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForExperimentalGenesisConfig')


def test_json_rpc_request_for_experimental_light_client_block_proof_encode_decode():
    data = load_mock_json('json_rpc_request_for_experimental_light_client_block_proof.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForExperimentalLightClientBlockProof')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForExperimentalLightClientBlockProof')


def test_json_rpc_request_for_experimental_light_client_proof_encode_decode():
    data = load_mock_json('json_rpc_request_for_experimental_light_client_proof.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForExperimentalLightClientProof')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForExperimentalLightClientProof')


def test_json_rpc_request_for_experimental_maintenance_windows_encode_decode():
    data = load_mock_json('json_rpc_request_for_experimental_maintenance_windows.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForExperimentalMaintenanceWindows')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForExperimentalMaintenanceWindows')


def test_json_rpc_request_for_experimental_protocol_config_encode_decode():
    data = load_mock_json('json_rpc_request_for_experimental_protocol_config.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForExperimentalProtocolConfig')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForExperimentalProtocolConfig')


def test_json_rpc_request_for_experimental_receipt_encode_decode():
    data = load_mock_json('json_rpc_request_for_experimental_receipt.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForExperimentalReceipt')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForExperimentalReceipt')


def test_json_rpc_request_for_experimental_split_storage_info_encode_decode():
    data = load_mock_json('json_rpc_request_for_experimental_split_storage_info.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForExperimentalSplitStorageInfo')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForExperimentalSplitStorageInfo')


def test_json_rpc_request_for_experimental_tx_status_encode_decode():
    data = load_mock_json('json_rpc_request_for_experimental_tx_status.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForExperimentalTxStatus')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForExperimentalTxStatus')


def test_json_rpc_request_for_experimental_validators_ordered_encode_decode():
    data = load_mock_json('json_rpc_request_for_experimental_validators_ordered.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForExperimentalValidatorsOrdered')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForExperimentalValidatorsOrdered')


def test_json_rpc_request_for_experimental_view_access_key_encode_decode():
    data = load_mock_json('json_rpc_request_for_experimental_view_access_key.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForExperimentalViewAccessKey')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForExperimentalViewAccessKey')


def test_json_rpc_request_for_experimental_view_access_key_list_encode_decode():
    data = load_mock_json('json_rpc_request_for_experimental_view_access_key_list.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForExperimentalViewAccessKeyList')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForExperimentalViewAccessKeyList')


def test_json_rpc_request_for_experimental_view_account_encode_decode():
    data = load_mock_json('json_rpc_request_for_experimental_view_account.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForExperimentalViewAccount')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForExperimentalViewAccount')


def test_json_rpc_request_for_experimental_view_code_encode_decode():
    data = load_mock_json('json_rpc_request_for_experimental_view_code.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForExperimentalViewCode')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForExperimentalViewCode')


def test_json_rpc_request_for_experimental_view_state_encode_decode():
    data = load_mock_json('json_rpc_request_for_experimental_view_state.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForExperimentalViewState')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForExperimentalViewState')


def test_json_rpc_request_for_block_encode_decode():
    data = load_mock_json('json_rpc_request_for_block.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForBlock')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForBlock')


def test_json_rpc_request_for_block_effects_encode_decode():
    data = load_mock_json('json_rpc_request_for_block_effects.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForBlockEffects')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForBlockEffects')


def test_json_rpc_request_for_broadcast_tx_async_encode_decode():
    data = load_mock_json('json_rpc_request_for_broadcast_tx_async.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForBroadcastTxAsync')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForBroadcastTxAsync')


def test_json_rpc_request_for_broadcast_tx_commit_encode_decode():
    data = load_mock_json('json_rpc_request_for_broadcast_tx_commit.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForBroadcastTxCommit')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForBroadcastTxCommit')


def test_json_rpc_request_for_changes_encode_decode():
    data = load_mock_json('json_rpc_request_for_changes.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForChanges')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForChanges')


def test_json_rpc_request_for_chunk_encode_decode():
    data = load_mock_json('json_rpc_request_for_chunk.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForChunk')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForChunk')


def test_json_rpc_request_for_client_config_encode_decode():
    data = load_mock_json('json_rpc_request_for_client_config.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForClientConfig')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForClientConfig')


def test_json_rpc_request_for_gas_price_encode_decode():
    data = load_mock_json('json_rpc_request_for_gas_price.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForGasPrice')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForGasPrice')


def test_json_rpc_request_for_genesis_config_encode_decode():
    data = load_mock_json('json_rpc_request_for_genesis_config.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForGenesisConfig')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForGenesisConfig')


def test_json_rpc_request_for_health_encode_decode():
    data = load_mock_json('json_rpc_request_for_health.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForHealth')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForHealth')


def test_json_rpc_request_for_light_client_proof_encode_decode():
    data = load_mock_json('json_rpc_request_for_light_client_proof.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForLightClientProof')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForLightClientProof')


def test_json_rpc_request_for_maintenance_windows_encode_decode():
    data = load_mock_json('json_rpc_request_for_maintenance_windows.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForMaintenanceWindows')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForMaintenanceWindows')


def test_json_rpc_request_for_network_info_encode_decode():
    data = load_mock_json('json_rpc_request_for_network_info.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForNetworkInfo')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForNetworkInfo')


def test_json_rpc_request_for_next_light_client_block_encode_decode():
    data = load_mock_json('json_rpc_request_for_next_light_client_block.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForNextLightClientBlock')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForNextLightClientBlock')


def test_json_rpc_request_for_query_encode_decode():
    data = load_mock_json('json_rpc_request_for_query.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForQuery')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForQuery')


def test_json_rpc_request_for_send_tx_encode_decode():
    data = load_mock_json('json_rpc_request_for_send_tx.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForSendTx')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForSendTx')


def test_json_rpc_request_for_status_encode_decode():
    data = load_mock_json('json_rpc_request_for_status.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForStatus')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForStatus')


def test_json_rpc_request_for_tx_encode_decode():
    data = load_mock_json('json_rpc_request_for_tx.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForTx')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForTx')


def test_json_rpc_request_for_validators_encode_decode():
    data = load_mock_json('json_rpc_request_for_validators.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcRequestForValidators')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcRequestForValidators')


def test_json_rpc_response_for_array_of_range_of_uint64_and_rpc_maintenance_windows_error_encode_decode():
    data = load_mock_json('json_rpc_response_for_array_of_range_of_uint64_and_rpc_maintenance_windows_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcResponseForArrayOfRangeOfUint64AndRpcMaintenanceWindowsError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcResponseForArrayOfRangeOfUint64AndRpcMaintenanceWindowsError')


def test_json_rpc_response_for_array_of_validator_stake_view_and_rpc_validator_error_encode_decode():
    data = load_mock_json('json_rpc_response_for_array_of_validator_stake_view_and_rpc_validator_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcResponseForArrayOfValidatorStakeViewAndRpcValidatorError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcResponseForArrayOfValidatorStakeViewAndRpcValidatorError')


def test_json_rpc_response_for_crypto_hash_and_rpc_transaction_error_encode_decode():
    data = load_mock_json('json_rpc_response_for_crypto_hash_and_rpc_transaction_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcResponseForCryptoHashAndRpcTransactionError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcResponseForCryptoHashAndRpcTransactionError')


def test_json_rpc_response_for_genesis_config_and_genesis_config_error_encode_decode():
    data = load_mock_json('json_rpc_response_for_genesis_config_and_genesis_config_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcResponseForGenesisConfigAndGenesisConfigError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcResponseForGenesisConfigAndGenesisConfigError')


def test_json_rpc_response_for_nullable_rpc_health_response_and_rpc_status_error_encode_decode():
    data = load_mock_json('json_rpc_response_for_nullable_rpc_health_response_and_rpc_status_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcResponseForNullableRpcHealthResponseAndRpcStatusError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcResponseForNullableRpcHealthResponseAndRpcStatusError')


def test_json_rpc_response_for_rpc_block_response_and_rpc_block_error_encode_decode():
    data = load_mock_json('json_rpc_response_for_rpc_block_response_and_rpc_block_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcResponseForRpcBlockResponseAndRpcBlockError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcResponseForRpcBlockResponseAndRpcBlockError')


def test_json_rpc_response_for_rpc_call_function_response_and_rpc_call_function_error_encode_decode():
    data = load_mock_json('json_rpc_response_for_rpc_call_function_response_and_rpc_call_function_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcResponseForRpcCallFunctionResponseAndRpcCallFunctionError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcResponseForRpcCallFunctionResponseAndRpcCallFunctionError')


def test_json_rpc_response_for_rpc_chunk_response_and_rpc_chunk_error_encode_decode():
    data = load_mock_json('json_rpc_response_for_rpc_chunk_response_and_rpc_chunk_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcResponseForRpcChunkResponseAndRpcChunkError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcResponseForRpcChunkResponseAndRpcChunkError')


def test_json_rpc_response_for_rpc_client_config_response_and_rpc_client_config_error_encode_decode():
    data = load_mock_json('json_rpc_response_for_rpc_client_config_response_and_rpc_client_config_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcResponseForRpcClientConfigResponseAndRpcClientConfigError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcResponseForRpcClientConfigResponseAndRpcClientConfigError')


def test_json_rpc_response_for_rpc_congestion_level_response_and_rpc_chunk_error_encode_decode():
    data = load_mock_json('json_rpc_response_for_rpc_congestion_level_response_and_rpc_chunk_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcResponseForRpcCongestionLevelResponseAndRpcChunkError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcResponseForRpcCongestionLevelResponseAndRpcChunkError')


def test_json_rpc_response_for_rpc_gas_price_response_and_rpc_gas_price_error_encode_decode():
    data = load_mock_json('json_rpc_response_for_rpc_gas_price_response_and_rpc_gas_price_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcResponseForRpcGasPriceResponseAndRpcGasPriceError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcResponseForRpcGasPriceResponseAndRpcGasPriceError')


def test_json_rpc_response_for_rpc_light_client_block_proof_response_and_rpc_light_client_proof_error_encode_decode():
    data = load_mock_json('json_rpc_response_for_rpc_light_client_block_proof_response_and_rpc_light_client_proof_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcResponseForRpcLightClientBlockProofResponseAndRpcLightClientProofError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcResponseForRpcLightClientBlockProofResponseAndRpcLightClientProofError')


def test_json_rpc_response_for_rpc_light_client_execution_proof_response_and_rpc_light_client_proof_error_encode_decode():
    data = load_mock_json('json_rpc_response_for_rpc_light_client_execution_proof_response_and_rpc_light_client_proof_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcResponseForRpcLightClientExecutionProofResponseAndRpcLightClientProofError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcResponseForRpcLightClientExecutionProofResponseAndRpcLightClientProofError')


def test_json_rpc_response_for_rpc_light_client_next_block_response_and_rpc_light_client_next_block_error_encode_decode():
    data = load_mock_json('json_rpc_response_for_rpc_light_client_next_block_response_and_rpc_light_client_next_block_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcResponseForRpcLightClientNextBlockResponseAndRpcLightClientNextBlockError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcResponseForRpcLightClientNextBlockResponseAndRpcLightClientNextBlockError')


def test_json_rpc_response_for_rpc_network_info_response_and_rpc_network_info_error_encode_decode():
    data = load_mock_json('json_rpc_response_for_rpc_network_info_response_and_rpc_network_info_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcResponseForRpcNetworkInfoResponseAndRpcNetworkInfoError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcResponseForRpcNetworkInfoResponseAndRpcNetworkInfoError')


def test_json_rpc_response_for_rpc_protocol_config_response_and_rpc_protocol_config_error_encode_decode():
    data = load_mock_json('json_rpc_response_for_rpc_protocol_config_response_and_rpc_protocol_config_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcResponseForRpcProtocolConfigResponseAndRpcProtocolConfigError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcResponseForRpcProtocolConfigResponseAndRpcProtocolConfigError')


def test_json_rpc_response_for_rpc_query_response_and_rpc_query_error_encode_decode():
    data = load_mock_json('json_rpc_response_for_rpc_query_response_and_rpc_query_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcResponseForRpcQueryResponseAndRpcQueryError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcResponseForRpcQueryResponseAndRpcQueryError')


def test_json_rpc_response_for_rpc_receipt_response_and_rpc_receipt_error_encode_decode():
    data = load_mock_json('json_rpc_response_for_rpc_receipt_response_and_rpc_receipt_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcResponseForRpcReceiptResponseAndRpcReceiptError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcResponseForRpcReceiptResponseAndRpcReceiptError')


def test_json_rpc_response_for_rpc_split_storage_info_response_and_rpc_split_storage_info_error_encode_decode():
    data = load_mock_json('json_rpc_response_for_rpc_split_storage_info_response_and_rpc_split_storage_info_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcResponseForRpcSplitStorageInfoResponseAndRpcSplitStorageInfoError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcResponseForRpcSplitStorageInfoResponseAndRpcSplitStorageInfoError')


def test_json_rpc_response_for_rpc_state_changes_in_block_by_type_response_and_rpc_state_changes_error_encode_decode():
    data = load_mock_json('json_rpc_response_for_rpc_state_changes_in_block_by_type_response_and_rpc_state_changes_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcResponseForRpcStateChangesInBlockByTypeResponseAndRpcStateChangesError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcResponseForRpcStateChangesInBlockByTypeResponseAndRpcStateChangesError')


def test_json_rpc_response_for_rpc_state_changes_in_block_response_and_rpc_state_changes_error_encode_decode():
    data = load_mock_json('json_rpc_response_for_rpc_state_changes_in_block_response_and_rpc_state_changes_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcResponseForRpcStateChangesInBlockResponseAndRpcStateChangesError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcResponseForRpcStateChangesInBlockResponseAndRpcStateChangesError')


def test_json_rpc_response_for_rpc_status_response_and_rpc_status_error_encode_decode():
    data = load_mock_json('json_rpc_response_for_rpc_status_response_and_rpc_status_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcResponseForRpcStatusResponseAndRpcStatusError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcResponseForRpcStatusResponseAndRpcStatusError')


def test_json_rpc_response_for_rpc_transaction_response_and_rpc_transaction_error_encode_decode():
    data = load_mock_json('json_rpc_response_for_rpc_transaction_response_and_rpc_transaction_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcResponseForRpcTransactionResponseAndRpcTransactionError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcResponseForRpcTransactionResponseAndRpcTransactionError')


def test_json_rpc_response_for_rpc_validator_response_and_rpc_validator_error_encode_decode():
    data = load_mock_json('json_rpc_response_for_rpc_validator_response_and_rpc_validator_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcResponseForRpcValidatorResponseAndRpcValidatorError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcResponseForRpcValidatorResponseAndRpcValidatorError')


def test_json_rpc_response_for_rpc_view_access_key_list_response_and_rpc_view_access_key_list_error_encode_decode():
    data = load_mock_json('json_rpc_response_for_rpc_view_access_key_list_response_and_rpc_view_access_key_list_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcResponseForRpcViewAccessKeyListResponseAndRpcViewAccessKeyListError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcResponseForRpcViewAccessKeyListResponseAndRpcViewAccessKeyListError')


def test_json_rpc_response_for_rpc_view_access_key_response_and_rpc_view_access_key_error_encode_decode():
    data = load_mock_json('json_rpc_response_for_rpc_view_access_key_response_and_rpc_view_access_key_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcResponseForRpcViewAccessKeyResponseAndRpcViewAccessKeyError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcResponseForRpcViewAccessKeyResponseAndRpcViewAccessKeyError')


def test_json_rpc_response_for_rpc_view_account_response_and_rpc_view_account_error_encode_decode():
    data = load_mock_json('json_rpc_response_for_rpc_view_account_response_and_rpc_view_account_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcResponseForRpcViewAccountResponseAndRpcViewAccountError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcResponseForRpcViewAccountResponseAndRpcViewAccountError')


def test_json_rpc_response_for_rpc_view_code_response_and_rpc_view_code_error_encode_decode():
    data = load_mock_json('json_rpc_response_for_rpc_view_code_response_and_rpc_view_code_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcResponseForRpcViewCodeResponseAndRpcViewCodeError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcResponseForRpcViewCodeResponseAndRpcViewCodeError')


def test_json_rpc_response_for_rpc_view_state_response_and_rpc_view_state_error_encode_decode():
    data = load_mock_json('json_rpc_response_for_rpc_view_state_response_and_rpc_view_state_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'JsonRpcResponseForRpcViewStateResponseAndRpcViewStateError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for JsonRpcResponseForRpcViewStateResponseAndRpcViewStateError')


def test_known_producer_view_encode_decode():
    data = load_mock_json('known_producer_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'KnownProducerView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for KnownProducerView')


def test_light_client_block_lite_view_encode_decode():
    data = load_mock_json('light_client_block_lite_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'LightClientBlockLiteView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for LightClientBlockLiteView')


def test_limit_config_encode_decode():
    data = load_mock_json('limit_config.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'LimitConfig')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for LimitConfig')


def test_log_summary_style_encode_decode():
    data = load_mock_json('log_summary_style.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'LogSummaryStyle')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for LogSummaryStyle')


def test_merkle_path_item_encode_decode():
    data = load_mock_json('merkle_path_item.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'MerklePathItem')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for MerklePathItem')


def test_method_resolve_error_encode_decode():
    data = load_mock_json('method_resolve_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'MethodResolveError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for MethodResolveError')


def test_missing_trie_value_encode_decode():
    data = load_mock_json('missing_trie_value.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'MissingTrieValue')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for MissingTrieValue')


def test_missing_trie_value_context_encode_decode():
    data = load_mock_json('missing_trie_value_context.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'MissingTrieValueContext')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for MissingTrieValueContext')


def test_mutable_config_value_encode_decode():
    data = load_mock_json('mutable_config_value.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'MutableConfigValue')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for MutableConfigValue')


def test_near_gas_encode_decode():
    data = load_mock_json('near_gas.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'NearGas')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for NearGas')


def test_near_token_encode_decode():
    data = load_mock_json('near_token.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'NearToken')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for NearToken')


def test_network_info_view_encode_decode():
    data = load_mock_json('network_info_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'NetworkInfoView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for NetworkInfoView')


def test_next_epoch_validator_info_encode_decode():
    data = load_mock_json('next_epoch_validator_info.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'NextEpochValidatorInfo')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for NextEpochValidatorInfo')


def test_non_delegate_action_encode_decode():
    data = load_mock_json('non_delegate_action.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'NonDelegateAction')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for NonDelegateAction')


def test_peer_id_encode_decode():
    data = load_mock_json('peer_id.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'PeerId')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for PeerId')


def test_peer_info_view_encode_decode():
    data = load_mock_json('peer_info_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'PeerInfoView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for PeerInfoView')


def test_prepare_error_encode_decode():
    data = load_mock_json('prepare_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'PrepareError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for PrepareError')


def test_protocol_version_check_config_encode_decode():
    data = load_mock_json('protocol_version_check_config.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ProtocolVersionCheckConfig')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ProtocolVersionCheckConfig')


def test_public_key_encode_decode():
    data = load_mock_json('public_key.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'PublicKey')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for PublicKey')


def test_range_of_uint64_encode_decode():
    data = load_mock_json('range_of_uint64.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RangeOfUint64')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RangeOfUint64')


def test_receipt_enum_view_encode_decode():
    data = load_mock_json('receipt_enum_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ReceiptEnumView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ReceiptEnumView')


def test_receipt_validation_error_encode_decode():
    data = load_mock_json('receipt_validation_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ReceiptValidationError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ReceiptValidationError')


def test_receipt_view_encode_decode():
    data = load_mock_json('receipt_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ReceiptView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ReceiptView')


def test_rpc_block_error_encode_decode():
    data = load_mock_json('rpc_block_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcBlockError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcBlockError')


def test_rpc_block_request_encode_decode():
    data = load_mock_json('rpc_block_request.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcBlockRequest')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcBlockRequest')


def test_rpc_block_response_encode_decode():
    data = load_mock_json('rpc_block_response.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcBlockResponse')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcBlockResponse')


def test_rpc_call_function_error_encode_decode():
    data = load_mock_json('rpc_call_function_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcCallFunctionError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcCallFunctionError')


def test_rpc_call_function_request_encode_decode():
    data = load_mock_json('rpc_call_function_request.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcCallFunctionRequest')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcCallFunctionRequest')


def test_rpc_call_function_response_encode_decode():
    data = load_mock_json('rpc_call_function_response.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcCallFunctionResponse')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcCallFunctionResponse')


def test_rpc_chunk_error_encode_decode():
    data = load_mock_json('rpc_chunk_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcChunkError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcChunkError')


def test_rpc_chunk_request_encode_decode():
    data = load_mock_json('rpc_chunk_request.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcChunkRequest')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcChunkRequest')


def test_rpc_chunk_response_encode_decode():
    data = load_mock_json('rpc_chunk_response.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcChunkResponse')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcChunkResponse')


def test_rpc_client_config_error_encode_decode():
    data = load_mock_json('rpc_client_config_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcClientConfigError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcClientConfigError')


def test_rpc_client_config_request_encode_decode():
    data = load_mock_json('rpc_client_config_request.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcClientConfigRequest')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcClientConfigRequest')


def test_rpc_client_config_response_encode_decode():
    data = load_mock_json('rpc_client_config_response.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcClientConfigResponse')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcClientConfigResponse')


def test_rpc_congestion_level_request_encode_decode():
    data = load_mock_json('rpc_congestion_level_request.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcCongestionLevelRequest')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcCongestionLevelRequest')


def test_rpc_congestion_level_response_encode_decode():
    data = load_mock_json('rpc_congestion_level_response.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcCongestionLevelResponse')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcCongestionLevelResponse')


def test_rpc_gas_price_error_encode_decode():
    data = load_mock_json('rpc_gas_price_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcGasPriceError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcGasPriceError')


def test_rpc_gas_price_request_encode_decode():
    data = load_mock_json('rpc_gas_price_request.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcGasPriceRequest')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcGasPriceRequest')


def test_rpc_gas_price_response_encode_decode():
    data = load_mock_json('rpc_gas_price_response.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcGasPriceResponse')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcGasPriceResponse')


def test_rpc_health_request_encode_decode():
    data = load_mock_json('rpc_health_request.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcHealthRequest')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcHealthRequest')


def test_rpc_health_response_encode_decode():
    data = load_mock_json('rpc_health_response.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcHealthResponse')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcHealthResponse')


def test_rpc_known_producer_encode_decode():
    data = load_mock_json('rpc_known_producer.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcKnownProducer')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcKnownProducer')


def test_rpc_light_client_block_proof_request_encode_decode():
    data = load_mock_json('rpc_light_client_block_proof_request.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcLightClientBlockProofRequest')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcLightClientBlockProofRequest')


def test_rpc_light_client_block_proof_response_encode_decode():
    data = load_mock_json('rpc_light_client_block_proof_response.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcLightClientBlockProofResponse')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcLightClientBlockProofResponse')


def test_rpc_light_client_execution_proof_request_encode_decode():
    data = load_mock_json('rpc_light_client_execution_proof_request.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcLightClientExecutionProofRequest')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcLightClientExecutionProofRequest')


def test_rpc_light_client_execution_proof_response_encode_decode():
    data = load_mock_json('rpc_light_client_execution_proof_response.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcLightClientExecutionProofResponse')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcLightClientExecutionProofResponse')


def test_rpc_light_client_next_block_error_encode_decode():
    data = load_mock_json('rpc_light_client_next_block_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcLightClientNextBlockError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcLightClientNextBlockError')


def test_rpc_light_client_next_block_request_encode_decode():
    data = load_mock_json('rpc_light_client_next_block_request.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcLightClientNextBlockRequest')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcLightClientNextBlockRequest')


def test_rpc_light_client_next_block_response_encode_decode():
    data = load_mock_json('rpc_light_client_next_block_response.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcLightClientNextBlockResponse')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcLightClientNextBlockResponse')


def test_rpc_light_client_proof_error_encode_decode():
    data = load_mock_json('rpc_light_client_proof_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcLightClientProofError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcLightClientProofError')


def test_rpc_maintenance_windows_error_encode_decode():
    data = load_mock_json('rpc_maintenance_windows_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcMaintenanceWindowsError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcMaintenanceWindowsError')


def test_rpc_maintenance_windows_request_encode_decode():
    data = load_mock_json('rpc_maintenance_windows_request.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcMaintenanceWindowsRequest')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcMaintenanceWindowsRequest')


def test_rpc_network_info_error_encode_decode():
    data = load_mock_json('rpc_network_info_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcNetworkInfoError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcNetworkInfoError')


def test_rpc_network_info_request_encode_decode():
    data = load_mock_json('rpc_network_info_request.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcNetworkInfoRequest')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcNetworkInfoRequest')


def test_rpc_network_info_response_encode_decode():
    data = load_mock_json('rpc_network_info_response.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcNetworkInfoResponse')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcNetworkInfoResponse')


def test_rpc_peer_info_encode_decode():
    data = load_mock_json('rpc_peer_info.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcPeerInfo')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcPeerInfo')


def test_rpc_protocol_config_error_encode_decode():
    data = load_mock_json('rpc_protocol_config_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcProtocolConfigError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcProtocolConfigError')


def test_rpc_protocol_config_request_encode_decode():
    data = load_mock_json('rpc_protocol_config_request.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcProtocolConfigRequest')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcProtocolConfigRequest')


def test_rpc_protocol_config_response_encode_decode():
    data = load_mock_json('rpc_protocol_config_response.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcProtocolConfigResponse')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcProtocolConfigResponse')


def test_rpc_query_error_encode_decode():
    data = load_mock_json('rpc_query_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcQueryError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcQueryError')


def test_rpc_query_request_encode_decode():
    data = load_mock_json('rpc_query_request.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcQueryRequest')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcQueryRequest')


def test_rpc_query_response_encode_decode():
    data = load_mock_json('rpc_query_response.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcQueryResponse')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcQueryResponse')


def test_rpc_receipt_error_encode_decode():
    data = load_mock_json('rpc_receipt_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcReceiptError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcReceiptError')


def test_rpc_receipt_request_encode_decode():
    data = load_mock_json('rpc_receipt_request.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcReceiptRequest')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcReceiptRequest')


def test_rpc_receipt_response_encode_decode():
    data = load_mock_json('rpc_receipt_response.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcReceiptResponse')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcReceiptResponse')


def test_rpc_request_validation_error_kind_encode_decode():
    data = load_mock_json('rpc_request_validation_error_kind.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcRequestValidationErrorKind')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcRequestValidationErrorKind')


def test_rpc_send_transaction_request_encode_decode():
    data = load_mock_json('rpc_send_transaction_request.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcSendTransactionRequest')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcSendTransactionRequest')


def test_rpc_split_storage_info_error_encode_decode():
    data = load_mock_json('rpc_split_storage_info_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcSplitStorageInfoError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcSplitStorageInfoError')


def test_rpc_split_storage_info_request_encode_decode():
    data = load_mock_json('rpc_split_storage_info_request.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcSplitStorageInfoRequest')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcSplitStorageInfoRequest')


def test_rpc_split_storage_info_response_encode_decode():
    data = load_mock_json('rpc_split_storage_info_response.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcSplitStorageInfoResponse')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcSplitStorageInfoResponse')


def test_rpc_state_changes_error_encode_decode():
    data = load_mock_json('rpc_state_changes_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcStateChangesError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcStateChangesError')


def test_rpc_state_changes_in_block_by_type_request_encode_decode():
    data = load_mock_json('rpc_state_changes_in_block_by_type_request.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcStateChangesInBlockByTypeRequest')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcStateChangesInBlockByTypeRequest')


def test_rpc_state_changes_in_block_by_type_response_encode_decode():
    data = load_mock_json('rpc_state_changes_in_block_by_type_response.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcStateChangesInBlockByTypeResponse')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcStateChangesInBlockByTypeResponse')


def test_rpc_state_changes_in_block_request_encode_decode():
    data = load_mock_json('rpc_state_changes_in_block_request.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcStateChangesInBlockRequest')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcStateChangesInBlockRequest')


def test_rpc_state_changes_in_block_response_encode_decode():
    data = load_mock_json('rpc_state_changes_in_block_response.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcStateChangesInBlockResponse')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcStateChangesInBlockResponse')


def test_rpc_status_error_encode_decode():
    data = load_mock_json('rpc_status_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcStatusError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcStatusError')


def test_rpc_status_request_encode_decode():
    data = load_mock_json('rpc_status_request.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcStatusRequest')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcStatusRequest')


def test_rpc_status_response_encode_decode():
    data = load_mock_json('rpc_status_response.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcStatusResponse')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcStatusResponse')


def test_rpc_transaction_error_encode_decode():
    data = load_mock_json('rpc_transaction_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcTransactionError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcTransactionError')


def test_rpc_transaction_response_encode_decode():
    data = load_mock_json('rpc_transaction_response.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcTransactionResponse')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcTransactionResponse')


def test_rpc_transaction_status_request_encode_decode():
    data = load_mock_json('rpc_transaction_status_request.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcTransactionStatusRequest')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcTransactionStatusRequest')


def test_rpc_validator_error_encode_decode():
    data = load_mock_json('rpc_validator_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcValidatorError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcValidatorError')


def test_rpc_validator_request_encode_decode():
    data = load_mock_json('rpc_validator_request.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcValidatorRequest')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcValidatorRequest')


def test_rpc_validator_response_encode_decode():
    data = load_mock_json('rpc_validator_response.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcValidatorResponse')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcValidatorResponse')


def test_rpc_validators_ordered_request_encode_decode():
    data = load_mock_json('rpc_validators_ordered_request.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcValidatorsOrderedRequest')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcValidatorsOrderedRequest')


def test_rpc_view_access_key_error_encode_decode():
    data = load_mock_json('rpc_view_access_key_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcViewAccessKeyError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcViewAccessKeyError')


def test_rpc_view_access_key_list_error_encode_decode():
    data = load_mock_json('rpc_view_access_key_list_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcViewAccessKeyListError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcViewAccessKeyListError')


def test_rpc_view_access_key_list_request_encode_decode():
    data = load_mock_json('rpc_view_access_key_list_request.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcViewAccessKeyListRequest')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcViewAccessKeyListRequest')


def test_rpc_view_access_key_list_response_encode_decode():
    data = load_mock_json('rpc_view_access_key_list_response.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcViewAccessKeyListResponse')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcViewAccessKeyListResponse')


def test_rpc_view_access_key_request_encode_decode():
    data = load_mock_json('rpc_view_access_key_request.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcViewAccessKeyRequest')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcViewAccessKeyRequest')


def test_rpc_view_access_key_response_encode_decode():
    data = load_mock_json('rpc_view_access_key_response.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcViewAccessKeyResponse')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcViewAccessKeyResponse')


def test_rpc_view_account_error_encode_decode():
    data = load_mock_json('rpc_view_account_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcViewAccountError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcViewAccountError')


def test_rpc_view_account_request_encode_decode():
    data = load_mock_json('rpc_view_account_request.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcViewAccountRequest')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcViewAccountRequest')


def test_rpc_view_account_response_encode_decode():
    data = load_mock_json('rpc_view_account_response.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcViewAccountResponse')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcViewAccountResponse')


def test_rpc_view_code_error_encode_decode():
    data = load_mock_json('rpc_view_code_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcViewCodeError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcViewCodeError')


def test_rpc_view_code_request_encode_decode():
    data = load_mock_json('rpc_view_code_request.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcViewCodeRequest')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcViewCodeRequest')


def test_rpc_view_code_response_encode_decode():
    data = load_mock_json('rpc_view_code_response.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcViewCodeResponse')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcViewCodeResponse')


def test_rpc_view_state_error_encode_decode():
    data = load_mock_json('rpc_view_state_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcViewStateError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcViewStateError')


def test_rpc_view_state_request_encode_decode():
    data = load_mock_json('rpc_view_state_request.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcViewStateRequest')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcViewStateRequest')


def test_rpc_view_state_response_encode_decode():
    data = load_mock_json('rpc_view_state_response.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RpcViewStateResponse')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RpcViewStateResponse')


def test_runtime_config_view_encode_decode():
    data = load_mock_json('runtime_config_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RuntimeConfigView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RuntimeConfigView')


def test_runtime_fees_config_view_encode_decode():
    data = load_mock_json('runtime_fees_config_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'RuntimeFeesConfigView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for RuntimeFeesConfigView')


def test_shard_id_encode_decode():
    data = load_mock_json('shard_id.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ShardId')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ShardId')


def test_shard_layout_encode_decode():
    data = load_mock_json('shard_layout.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ShardLayout')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ShardLayout')


def test_shard_layout_v0_encode_decode():
    data = load_mock_json('shard_layout_v0.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ShardLayoutV0')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ShardLayoutV0')


def test_shard_layout_v1_encode_decode():
    data = load_mock_json('shard_layout_v1.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ShardLayoutV1')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ShardLayoutV1')


def test_shard_layout_v2_encode_decode():
    data = load_mock_json('shard_layout_v2.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ShardLayoutV2')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ShardLayoutV2')


def test_shard_layout_v3_encode_decode():
    data = load_mock_json('shard_layout_v3.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ShardLayoutV3')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ShardLayoutV3')


def test_shard_uid_encode_decode():
    data = load_mock_json('shard_uid.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ShardUId')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ShardUId')


def test_signature_encode_decode():
    data = load_mock_json('signature.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'Signature')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for Signature')


def test_signed_delegate_action_encode_decode():
    data = load_mock_json('signed_delegate_action.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'SignedDelegateAction')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for SignedDelegateAction')


def test_signed_transaction_encode_decode():
    data = load_mock_json('signed_transaction.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'SignedTransaction')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for SignedTransaction')


def test_signed_transaction_view_encode_decode():
    data = load_mock_json('signed_transaction_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'SignedTransactionView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for SignedTransactionView')


def test_slashed_validator_encode_decode():
    data = load_mock_json('slashed_validator.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'SlashedValidator')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for SlashedValidator')


def test_stake_action_encode_decode():
    data = load_mock_json('stake_action.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'StakeAction')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for StakeAction')


def test_state_change_cause_view_encode_decode():
    data = load_mock_json('state_change_cause_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'StateChangeCauseView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for StateChangeCauseView')


def test_state_change_kind_view_encode_decode():
    data = load_mock_json('state_change_kind_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'StateChangeKindView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for StateChangeKindView')


def test_state_change_with_cause_view_encode_decode():
    data = load_mock_json('state_change_with_cause_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'StateChangeWithCauseView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for StateChangeWithCauseView')


def test_state_item_encode_decode():
    data = load_mock_json('state_item.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'StateItem')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for StateItem')


def test_state_sync_config_encode_decode():
    data = load_mock_json('state_sync_config.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'StateSyncConfig')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for StateSyncConfig')


def test_status_sync_info_encode_decode():
    data = load_mock_json('status_sync_info.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'StatusSyncInfo')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for StatusSyncInfo')


def test_storage_error_encode_decode():
    data = load_mock_json('storage_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'StorageError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for StorageError')


def test_storage_get_mode_encode_decode():
    data = load_mock_json('storage_get_mode.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'StorageGetMode')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for StorageGetMode')


def test_storage_usage_config_view_encode_decode():
    data = load_mock_json('storage_usage_config_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'StorageUsageConfigView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for StorageUsageConfigView')


def test_store_key_encode_decode():
    data = load_mock_json('store_key.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'StoreKey')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for StoreKey')


def test_store_value_encode_decode():
    data = load_mock_json('store_value.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'StoreValue')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for StoreValue')


def test_sync_checkpoint_encode_decode():
    data = load_mock_json('sync_checkpoint.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'SyncCheckpoint')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for SyncCheckpoint')


def test_sync_concurrency_encode_decode():
    data = load_mock_json('sync_concurrency.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'SyncConcurrency')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for SyncConcurrency')


def test_sync_config_encode_decode():
    data = load_mock_json('sync_config.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'SyncConfig')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for SyncConfig')


def test_tier1proxy_view_encode_decode():
    data = load_mock_json('tier1proxy_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'Tier1ProxyView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for Tier1ProxyView')


def test_tracked_shards_config_encode_decode():
    data = load_mock_json('tracked_shards_config.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'TrackedShardsConfig')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for TrackedShardsConfig')


def test_transfer_action_encode_decode():
    data = load_mock_json('transfer_action.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'TransferAction')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for TransferAction')


def test_transfer_to_gas_key_action_encode_decode():
    data = load_mock_json('transfer_to_gas_key_action.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'TransferToGasKeyAction')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for TransferToGasKeyAction')


def test_tx_execution_error_encode_decode():
    data = load_mock_json('tx_execution_error.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'TxExecutionError')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for TxExecutionError')


def test_tx_execution_status_encode_decode():
    data = load_mock_json('tx_execution_status.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'TxExecutionStatus')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for TxExecutionStatus')


def test_use_global_contract_action_encode_decode():
    data = load_mock_json('use_global_contract_action.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'UseGlobalContractAction')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for UseGlobalContractAction')


def test_vmconfig_view_encode_decode():
    data = load_mock_json('vmconfig_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'VMConfigView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for VMConfigView')


def test_vmkind_encode_decode():
    data = load_mock_json('vmkind.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'VMKind')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for VMKind')


def test_validator_info_encode_decode():
    data = load_mock_json('validator_info.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ValidatorInfo')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ValidatorInfo')


def test_validator_kickout_reason_encode_decode():
    data = load_mock_json('validator_kickout_reason.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ValidatorKickoutReason')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ValidatorKickoutReason')


def test_validator_kickout_view_encode_decode():
    data = load_mock_json('validator_kickout_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ValidatorKickoutView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ValidatorKickoutView')


def test_validator_stake_view_encode_decode():
    data = load_mock_json('validator_stake_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ValidatorStakeView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ValidatorStakeView')


def test_validator_stake_view_v1_encode_decode():
    data = load_mock_json('validator_stake_view_v1.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ValidatorStakeViewV1')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ValidatorStakeViewV1')


def test_version_encode_decode():
    data = load_mock_json('version.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'Version')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for Version')


def test_view_state_result_encode_decode():
    data = load_mock_json('view_state_result.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'ViewStateResult')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for ViewStateResult')


def test_wasm_trap_encode_decode():
    data = load_mock_json('wasm_trap.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'WasmTrap')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for WasmTrap')


def test_withdraw_from_gas_key_action_encode_decode():
    data = load_mock_json('withdraw_from_gas_key_action.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'WithdrawFromGasKeyAction')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for WithdrawFromGasKeyAction')


def test_witness_config_view_encode_decode():
    data = load_mock_json('witness_config_view.json')

    try:
        model_cls = getattr(near_jsonrpc_models, 'WitnessConfigView')
        obj1 = model_cls.model_validate_json(data)
        json2 = obj1.model_dump_json()
        obj2 = model_cls.model_validate_json(json2)

        assert obj1 == obj2
    except Exception as e:
        pytest.fail(f'Serialization test failed for WitnessConfigView')

