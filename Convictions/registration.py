# registration.py

async def register_user(ctx, registered_users):
    if ctx.author.id in registered_users:
        await ctx.send('You are already registered.')
    else:
        # Add the user to the list of registered users
        registered_users.add(ctx.author.id)
        
        # Save the updated list back to the accounts.txt file
        with open('Assets/accounts.txt', 'a') as file:
            file.write(str(ctx.author.id) + '\n')
        
        await ctx.send('You are now registered.')
