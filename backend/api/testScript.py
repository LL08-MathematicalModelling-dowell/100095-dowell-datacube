from bson import BSON

# Get the BSON spec for supported types
bson_spec = BSON().document_class._type_registry
supported_types = [t.__name__ for t in bson_spec.values()]
print("Supported BSON Types:", supported_types)
