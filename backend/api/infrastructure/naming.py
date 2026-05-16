# api/utils/naming.py

def generate_db_name(user_provided_name: str, user_id: str) -> str:
    """
    Generates a unique, internal database name based on the user's input
    and their unique ID.
    
    Example:
    user_provided_name = "customer_project"
    user_id = "66a1b2c3d4e5f6a7b8c9d0e1"
    Returns: "customer_project_66a1b2_V2"
    """
    if not user_provided_name or not user_id:
        raise ValueError("Both user_provided_name and user_id are required.")

    # Sanitize the user-provided name (remove spaces, special chars, etc.)
    # This is a simple example; you can make it more robust.
    sanitized_name = user_provided_name.lower().replace(" ", "_")
    
    # Take the first 6 characters of the user's ObjectId string for uniqueness
    user_id_prefix = str(user_id)[:6]
    
    # Construct the final internal name
    internal_name = f"{sanitized_name}_{user_id_prefix}_V2"
    
    return internal_name

def get_user_provided_name(internal_db_name: str) -> str:
    """
    Reverses the process, extracting the user-provided name from the
    internal database name.
    
    Example:
    internal_db_name = "customer_project_66a1b2_V2"
    Returns: "customer_project"
    """
    if not internal_db_name.endswith("_V2"):
        # Not a V2-formatted name, return as is or handle as an error
        return internal_db_name
        
    # Split the string from the right, once, at the last underscore
    parts = internal_db_name.rsplit('_', 2)
    
    # The user-provided name is the first part of the split
    if len(parts) == 3:
        return parts[0]
    
    # Fallback if the format is unexpected
    return internal_db_name