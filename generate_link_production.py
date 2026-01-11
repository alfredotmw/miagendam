from auth.jwt import create_access_token, SECRET_KEY
import os

def generate_production_link():
    print("\n=== GENERADOR DE LINK DE EXCEL (PRODUCCIÓN) ===\n")
    print(f"Clave Secreta Actual (detectada): {SECRET_KEY}")
    print("Si en Render usas una variable de entorno SECRET_KEY diferente, el token generado aquí NO funcionará allá a menos que coincidan.\n")
    
    use_custom = input("¿Deseas ingresar una SECRET_KEY manual para generar el token? (s/n): ").lower().strip()
    
    secret_to_use = SECRET_KEY
    if use_custom == 's':
        secret_to_use = input("Ingresa la SECRET_KEY exacta de Render: ").strip()
        # Hack temporal para usar la clave custom solo para esta generación sin romper el import
        import auth.jwt
        auth.jwt.SECRET_KEY = secret_to_use
        print(f"✅ Usando clave personalizada: {secret_to_use[:4]}...{secret_to_use[-4:]}")

    # Generate token valid for 365 days
    expires = 60 * 24 * 365
    token = create_access_token(
        data={"sub": "admin", "role": "ADMIN"}, 
        expires_minutes=expires
    )
    
    base_url = "https://agendas-medicas.onrender.com"
    full_link = f"{base_url}/radioterapia/feed?token={token}"
    
    print("\n" + "="*60)
    print("🔗 LINK GENERADO PARA EXCEL / POWER BI:")
    print("="*60)
    print(full_link)
    print("="*60 + "\n")
    
    # Save to file just in case
    with open("link_production.txt", "w") as f:
        f.write(full_link)
    print("Guardado en link_production.txt")

if __name__ == "__main__":
    generate_production_link()
