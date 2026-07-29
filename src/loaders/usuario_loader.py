from src.database import GET_conexion

def SAVE_user_db(usuario:dict) -> dict:

    conexion = GET_conexion()

    if not conexion:
        return {"exito": False, "mensaje": "No se pudo establecer conexión con la base de datos"}

    cursor = conexion.cursor()

    try:

        sql_user = """
            INSERT INTO usuario (
                nombres, apellidos, tipo_documento, num_documento, num_telefono,
                correo, contrasena, id_rol
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)        
        """
        valores_user = (

            usuario["nombres"],
            usuario["apellidos"],
            usuario["tipo_documento"],
            usuario["num_documento"],
            usuario["num_telefono"],
            usuario["correo"],
            usuario["contrasena"],
            usuario["id_rol"],
        )

        cursor.execute(sql_user, valores_user)

        user_id = cursor.lastrowid

        conexion.commit()
        print(f"✅✅ El usuario {user_id} fue registrado con éxito. ✅✅")
        return {
            "exito" : True,
            "mensaje" : "✅✅ Usuario guardado exitosamente. ✅✅",
            "id_generado" : user_id
        }
    
    except Exception as us:
        conexion.rollback()
        print (f"❌❌ Error al intentar guardar usuario en la base de datos: {us}. ❌❌")
        return {"exito" : False, "mensaje" : f"❌❌ Error en la base de datos : {us} ❌❌"}

    finally:
        cursor.close()
        conexion.close()
