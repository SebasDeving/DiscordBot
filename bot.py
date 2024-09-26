import discord
from discord.ext import commands
import asyncio
import os
import webserver

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Diccionario para almacenar información de los usuarios
usuarios = {}

# Lista de tiempos de cárcel para cada advertencia
tiempos_carcel = [30, 60, 120, 240, 1440]  # en minutos

def tiene_rol_autorizado():
    async def predicate(ctx):
        roles_autorizados = [1276677810479697980, 1282913486023692371, 1277266141781295155]  # Reemplaza con los IDs reales
        return any(role.id in roles_autorizados for role in ctx.author.roles)
    return commands.check(predicate)

@bot.event
async def on_ready():
    print(f'{bot.user} ha conectado a Discord!')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("No tienes permiso para usar este comando. Necesitas tener uno de los siguientes roles: Community mod, Among us mod, o Among us admin.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("Comando no reconocido. Por favor, verifica que hayas escrito el comando correctamente.")
    else:
        # Imprimir el error en la consola para debugging
        print(f"Ocurrió un error no manejado: {type(error).__name__}: {error}")
        await ctx.send("Ocurrió un error al procesar el comando. Por favor, inténtalo de nuevo más tarde.")

@bot.command()
@tiene_rol_autorizado()
async def encarcelar(ctx, nombre_usuario: str, *, motivo: str):
    global usuarios
    if nombre_usuario not in usuarios:
        usuarios[nombre_usuario] = {"advertencias": 0, "en_carcel": False}
    
    usuarios[nombre_usuario]["advertencias"] += 1
    usuarios[nombre_usuario]["en_carcel"] = True
    num_advertencia = usuarios[nombre_usuario]["advertencias"]
    
    # Buscar al usuario por nombre
    usuario = discord.utils.get(ctx.guild.members, name=nombre_usuario)
    mencion = usuario.mention if usuario else nombre_usuario
    
    # Determinar el tiempo de cárcel y la próxima sanción
    if num_advertencia <= 5:
        tiempo_carcel = tiempos_carcel[num_advertencia - 1]
        proxima_sancion = f"{tiempos_carcel[num_advertencia] // 60} horas" if num_advertencia < 5 else "Expulsión"
    else:
        tiempo_carcel = tiempos_carcel[-1]
        proxima_sancion = "Expulsión"

    # Convertir tiempo de cárcel a formato legible
    tiempo_legible = f"{tiempo_carcel // 60} horas" if tiempo_carcel >= 60 else f"{tiempo_carcel} minutos"

    # Enviar mensaje al canal de cárcel
    canal_carcel = bot.get_channel(1286768404245512244)  # Asegúrate de reemplazar este ID con el correcto
    await canal_carcel.send(f"Usuario: {mencion}\n"
                            f"Motivo: {motivo}\n"
                            f"Advertencia N°: {num_advertencia}\n"
                            f"Tiempo de cárcel: {tiempo_legible} en la cárcel\n"
                            f"Próxima Sanción: {proxima_sancion} en la cárcel\n")

    # Enviar mensaje de confirmación al canal donde se ejecutó el comando
    await ctx.send(f"{nombre_usuario} ha sido encarcelado por {tiempo_legible}. {motivo}")

    # Liberar al jugador después del tiempo especificado
    await asyncio.sleep(tiempo_carcel * 60)  # Convertir minutos a segundos
    if usuarios[nombre_usuario]["en_carcel"]:
        usuarios[nombre_usuario]["en_carcel"] = False
        await ctx.send(f"{nombre_usuario} ha sido liberado de la cárcel.")

@bot.command()
@tiene_rol_autorizado()
async def liberar(ctx, nombre_usuario: str):
    global usuarios
    usuario = discord.utils.get(ctx.guild.members, name=nombre_usuario)
    
    if nombre_usuario in usuarios and usuarios[nombre_usuario]["en_carcel"]:
        usuarios[nombre_usuario]["en_carcel"] = False
        
        if usuario:
            await ctx.send(f"{usuario.name} ha sido liberado de la cárcel.")
        else:
            await ctx.send(f"{nombre_usuario} ha sido liberado de la cárcel, pero no se encuentra en el servidor.")
    else:
        await ctx.send(f"{nombre_usuario} no está en la cárcel.")

# Ejecuta el bot
webserver.keep_alive()
bot.run(DISCORD_TOKEN)

