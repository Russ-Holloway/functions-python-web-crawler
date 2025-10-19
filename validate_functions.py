"""
Quick validation script to check if function_app.py is properly structured
"""
import sys
import importlib.util

def validate_function_app():
    """Validate function_app.py structure"""
    print("🔍 Validating function_app.py...")
    
    try:
        # Load the module
        spec = importlib.util.spec_from_file_location("function_app", "function_app.py")
        if spec is None or spec.loader is None:
            print("❌ Could not load function_app.py")
            return False
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Check if app exists
        if not hasattr(module, 'app'):
            print("❌ ERROR: 'app' object not found in function_app.py")
            return False
        
        print("✅ 'app' object found")
        
        # Check if there's a 'main' (which shouldn't exist in v2)
        if hasattr(module, 'main'):
            print("⚠️  WARNING: 'main' variable found (should not exist in Python v2 model)")
            return False
        else:
            print("✅ No 'main' variable (correct for Python v2)")
        
        # Check app type
        app = getattr(module, 'app')
        app_type = type(app).__name__
        print(f"✅ App type: {app_type}")
        
        # Try to get registered functions
        if hasattr(app, '_function_builders'):
            func_count = len(app._function_builders)
            print(f"✅ Found {func_count} registered functions")
            
            # List function names
            print("\n📋 Registered Functions:")
            for i, builder in enumerate(app._function_builders, 1):
                func_name = builder._name if hasattr(builder, '_name') else 'Unknown'
                print(f"   {i}. {func_name}")
        else:
            print("⚠️  Could not access function builders")
        
        print("\n✅ Validation PASSED - function_app.py is properly structured!")
        return True
        
    except SyntaxError as e:
        print(f"❌ SYNTAX ERROR: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = validate_function_app()
    sys.exit(0 if success else 1)
