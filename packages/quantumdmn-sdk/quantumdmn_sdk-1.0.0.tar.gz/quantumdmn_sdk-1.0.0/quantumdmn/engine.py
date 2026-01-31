from typing import Dict, Optional, Any
from quantumdmn.api.default_api import DefaultApi
from quantumdmn.model.feel_value import FeelValue
from quantumdmn.models.evaluate_stored_request import EvaluateStoredRequest
from quantumdmn.api_client import ApiClient
from quantumdmn.models.evaluation_result import EvaluationResult
class DmnEngine:
    def __init__(self, api_client: ApiClient, project_id: str):
        self.api = DefaultApi(api_client)
        self.project_id = project_id

    def evaluate(self, definition_id: str, context: Dict[str, Any], version: Optional[int] = None) -> EvaluationResult:
        """
        Evaluate a stored DMN definition.
        
        Args:
            definition_id: The UUID or XML ID of the definition.
            context: A dictionary of inputs (Python types or FeelValue).
            version: Optional version number.
            
        Returns:
            A dictionary of results.
        """
        # Convert context values to FeelValue if needed
        feel_context = {}
        for k, v in context.items():
            if isinstance(v, FeelValue):
                feel_context[k] = v
            else:
                feel_context[k] = FeelValue.from_python(v)
        
        # Since our mapped FeelValue is 'object' in the generated code for properties,
        # we might need to be careful about what the generated model expects.
        # But 'EvaluateStoredRequest' has 'context' which is 'FeelContext'.
        # 'FeelContext' is mapped to 'Dict[str, FeelValue]' (effectively).
        # We need to make sure the serializer calls 'to_dict' on our objects.
        
        req = EvaluateStoredRequest(
            context=feel_context,
            version=version
        )
        
        # We assume the library handles definition_id as UUID string
        # If definition_id is not a UUID, we might need the 'by-xml-id' endpoint,
        # but the current generated client splits them.
        # For simplicity, we'll try the standard endpoint.
        # TODO: Detect XML ID and use alternate endpoint if needed.
        
        # Determine if it's a UUID (approximation)
        if len(definition_id) == 36 and "-" in definition_id:
             result = self.api.evaluate_stored(
                 project_id=self.project_id,
                 definition_id=definition_id,
                 evaluate_stored_request=req
             )
        else:
            # Not supported easily without checking endpoints.
            # Assuming UUID for now or user uses `by_xml_id` directly on API.
            # Or we can implement the logic here.
             result = self.api.evaluate_by_xmlid(
                 project_id=self.project_id,
                 xml_definition_id=definition_id,
                 evaluate_stored_request=req,
                 version=version
             )

        # Unwrap results
        # result is a Dict[str, EvaluationResult]
        # EvaluationResult.value is FeelValue (mapped)
        
        unwrapped = {}
        if result:
            for k, v in result.items():
                 # v is EvaluationResult
                 if v.value:
                      unwrapped[k] = v.value.to_raw()
                 else:
                      unwrapped[k] = None
        
        return result
