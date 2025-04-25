# """
# Utility functions for JSON serialization of datetime objects.
# Used by the Supabase client to properly serialize Python objects.
# """

# import json
# import datetime
# from typing import Any, Dict, List, Union, Optional

# class DateTimeEncoder(json.JSONEncoder):
#     """
#     Custom JSON encoder that handles datetime objects by converting them to ISO format strings.
#     """
#     def default(self, obj: Any) -> Any:
#         if isinstance(obj, datetime.datetime):
#             return obj.isoformat()
#         elif isinstance(obj, datetime.date):
#             return obj.isoformat()
#         elif isinstance(obj, datetime.time):
#             return obj.isoformat()
#         return super().default(obj)

# def serialize_for_supabase(data: Union[Dict, List]) -> Union[Dict, List]:
#     """
#     Serializes data for Supabase, handling datetime objects and other complex types.
    
#     Args:
#         data: Dictionary or list to be serialized
        
#     Returns:
#         Serialized data safe for JSON conversion and Supabase storage
#     """
#     if isinstance(data, dict):
#         # Process dictionary items
#         result = {}
#         for key, value in data.items():
#             # Handle datetime objects
#             if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
#                 result[key] = value.isoformat()
#             # Handle nested dictionaries
#             elif isinstance(value, dict):
#                 result[key] = serialize_for_supabase(value)
#             # Handle lists
#             elif isinstance(value, list):
#                 result[key] = serialize_for_supabase(value)
#             # Handle other objects that might not be JSON serializable
#             elif hasattr(value, '__dict__'):
#                 try:
#                     # Try to convert to dict first
#                     result[key] = serialize_for_supabase(value.__dict__)
#                 except:
#                     # Fall back to string representation
#                     result[key] = str(value)
#             else:
#                 result[key] = value
#         return result
    
#     elif isinstance(data, list):
#         # Process list items
#         result = []
#         for item in data:
#             if isinstance(item, (datetime.datetime, datetime.date, datetime.time)):
#                 result.append(item.isoformat())
#             elif isinstance(item, dict):
#                 result.append(serialize_for_supabase(item))
#             elif isinstance(item, list):
#                 result.append(serialize_for_supabase(item))
#             elif hasattr(item, '__dict__'):
#                 try:
#                     result.append(serialize_for_supabase(item.__dict__))
#                 except:
#                     result.append(str(item))
#             else:
#                 result.append(item)
#         return result
    
#     # If it's neither a dict nor a list, return as is
#     return data

# def json_dumps_with_datetime(data: Any) -> str:
#     """
#     Dumps data to JSON string, properly handling datetime objects.
    
#     Args:
#         data: Data to be converted to JSON
        
#     Returns:
#         JSON string representation
#     """
#     return json.dumps(data, cls=DateTimeEncoder) 