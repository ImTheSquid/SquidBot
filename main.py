import getopt
import json
import sys
from os import path

import discord


class JSONLoader:
    config = {'token': '', 'motm': '', 'custom-responses': {}, 'lock-channel-custom-resp': 'True', 'removal-filter': [],
              'prefix': '', 'channel': ''}

    def __init__(self, init_args: dict, gen_config: bool = False):
        if 'token' in init_args:
            self.config['token'] = init_args['token']
        elif 'motm' in init_args:
            self.config['motm'] = init_args['motm']
        elif 'prefix' in init_args:
            self.config['prefix'] = init_args['prefix']
        elif 'lock-channel-custom-resp' in init_args:
            self.config['lock-channel-custom-resp'] = init_args['lock-channel-custom-resp']

        if gen_config:
            self.generate_config()

    def generate_config(self):
        with open('config.json', 'w') as f:
            json.dump(self.config, f)

    def load_config(self):
        with open('config.json', 'r') as f:
            self.config = json.load(f)

    def get_prefix(self) -> str:
        return self.config['prefix']

    def get_motm(self) -> str:
        return self.config['motm']

    def get_custom_responses(self) -> dict:
        return self.config['custom-responses']

    def get_removal_filter(self) -> []:
        return self.config['removal-filter']

    def get_token(self) -> str:
        return self.config['token']

    def get_channel(self) -> str:
        return self.config['channel']

    # Whether to allow custom responses only on specified channel or on all channels
    def get_lock_channel_responses(self) -> bool:
        return self.config['lock-channel-custom-resp'] == 'True'

    def set_lock_channel(self, lock: bool):
        self.config['lock-channel-custom-resp'] = 'True' if lock else 'False'
        self.generate_config()

    def set_channel(self, channel: str):
        self.config['channel'] = channel
        self.generate_config()

    def set_prefix(self, prefix: str):
        self.config['prefix'] = prefix
        self.generate_config()

    def add_filter(self, to_filter: str) -> bool:
        if to_filter not in self.config['removal-filter']:
            self.config['removal-filter'].append(to_filter)
            self.generate_config()
            return True
        return False

    def remove_filter(self, to_remove: str) -> bool:
        if to_remove in self.config['removal-filter']:
            self.config['removal-filter'].remove(to_remove)
            self.generate_config()
            return True
        return False

    def add_response(self, key: str, value: str):
        self.config['custom-responses'][key] = value
        self.generate_config()

    def remove_response(self, key: str) -> bool:
        out = self.config['custom-responses'].pop(key, None)
        self.generate_config()
        return out is not None

    def set_motm(self, motm: str):
        self.config['motm'] = motm
        self.generate_config()


class Client(discord.Client):
    loader = None
    prefix = 'sb!'

    async def on_ready(self):
        if self.loader is None:
            print('Failed to load JSON loader, exiting...')
            await self.logout()
            sys.exit(0)
        if len(self.loader.get_prefix()) > 0:
            self.prefix = self.loader.get_prefix()
        print('Logged on as {0}! Using prefix:"{1}"'.format(self.user, self.prefix))
        if len(self.loader.get_channel()) > 0:
            channelNames = [n.name for n in self.get_all_channels()]
            if self.loader.get_channel() not in channelNames:
                return
            else:
                channels = [c for c in self.get_all_channels()]
                await channels[channelNames.index(self.loader.get_channel())].send(':white_check_mark: '
                                                                                   'Initialization '
                                                                                   'successful.')

    async def on_message(self, message):
        roleNames = [n.name for n in message.author.roles]
        command = message.content[len(self.prefix):]
        # Message filter
        if not message.author == self.user and 'Bot Manager' not in roleNames:
            for remove in self.loader.get_removal_filter():
                if remove in message.content:
                    await message.delete()
                    return
        # Custom responses
        if not message.author == self.user and 'remove-response' not in command and \
                not self.loader.get_lock_channel_responses():
            message_split = message.content.split(' ')
            for key in self.loader.get_custom_responses():
                if key in message_split:
                    await message.channel.send(self.loader.get_custom_responses()[key])
                    break
        # Return if no prefix or not in correct channel
        if not message.content.startswith(self.prefix) or (len(self.loader.get_channel()) > 0
                                                           and not message.channel.name == self.loader.get_channel()):
            return

        print('Message from {0.author}: {0.content}'.format(message))

        if command == 'help':
            embed = discord.Embed(title="Help", description='All commands marked with "*" require the "Bot Manager" '
                                                            'role. If you do not have that role and try to use one of '
                                                            'the *\'d commands, the bot will not respond.',
                                  color=0x4287f5)
            embed.add_field(name="motm", value="Prints Message of the Month.", inline=False)
            embed.add_field(name='smotm', value='* Sets Message of the Month', inline=False)
            embed.add_field(name="set-prefix <prefix>", value="* Sets prefix that the bot responds to.", inline=False)
            embed.add_field(name="set-channel <channel>", value="* Sets sole response channel. Pass '~' to respond to "
                                                                "all channels.",
                            inline=False)
            embed.add_field(name='get-removal-filter', value='* Prints terms that are set to be automatically deleted.',
                            inline=False)
            embed.add_field(name='add-filter <filter-item>', value='* Adds a term to be filtered.', inline=False)
            embed.add_field(name='remove-filter <filter-item>', value='* Removes a term from the filter list.',
                            inline=False)
            embed.add_field(name='lock-responses [boolean]', value='* Locks custom responses to selected '
                                                                   'channel if any channel is set. Leaving out a '
                                                                   'boolean argument will print the current setting.',
                            inline=False)
            embed.add_field(name='custom-responses', value='* Prints custom responses.', inline=False)
            embed.add_field(name='add-response <key> <response>', value='* Adds a custom response.', inline=False)
            embed.add_field(name='remove-response <key>', value='* Removes a custom response.', inline=False)
            embed.add_field(name="exit", value="* Exits bot.", inline=False)
            embed.add_field(name="help", value="Prints help document.", inline=False)
            await message.channel.send(embed=embed)
        elif command == 'motm':
            if len(self.loader.get_motm()) > 0:
                await message.channel.send(self.loader.get_motm())
            else:
                await message.channel.send(':x: MOTM not set.')
        elif 'set-channel' in command and 'Bot Manager' in roleNames:
            if not len(command.split(' ')) == 2:
                await message.channel.send(':x: Incorrect number of arguments.')
                return

            channel = command.split(' ')[1]
            # Accept all channels
            if channel == '~':
                await message.channel.send(':white_check_mark: Set to accept all channels.')
                self.loader.set_channel('')
                return
            channelNames = [n.name for n in self.get_all_channels()]
            if channel not in channelNames:
                await message.channel.send(':x: Invalid channel.')
            else:
                await message.channel.send(':white_check_mark: Channel set to #{0}.'.format(channel))
                self.loader.set_channel(channel)
        elif 'set-prefix' in command and 'Bot Manager' in roleNames:
            if not len(command.split(' ')) == 2:
                await message.channel.send(':x: Incorrect number of arguments.')
                return

            self.loader.set_prefix(command.split(' ')[1])
            await message.channel.send('Prefix set to "{0}"'.format(self.loader.get_prefix()))
        elif command == 'get-removal-filter' and 'Bot Manager' in roleNames:
            if len(self.loader.get_removal_filter()) == 0:
                await message.channel.send(':x: Nothing on removal filter.')
            else:
                out_str = ''
                for item in self.loader.get_removal_filter():
                    out_str += '<' + item + '>\n'
                await message.channel.send(':no_entry: Removal list:\n```{0}```'.format(out_str))
        elif 'add-filter' in command and 'Bot Manager' in roleNames:
            if not len(command.split(' ')) >= 2:
                await message.channel.send(':x: Incorrect number of arguments.')
                return

            to_filter = command.split(' ')[1:]
            full_str = ' '.join(to_filter)
            if self.loader.add_filter(full_str):
                await message.channel.send(':white_check_mark: Filter added.')
            else:
                await message.channel.send(':x: Filter already exists.')
        elif 'remove-filter' in command and 'Bot Manager' in roleNames:
            if not len(command.split(' ')) >= 2:
                await message.channel.send(':x: Incorrect number of arguments.')
                return

            rm_filter = command.split(' ')[1:]
            full_str = ' '.join(rm_filter)
            if self.loader.remove_filter(full_str):
                await message.channel.send(':white_check_mark: Filter removed.')
            else:
                await message.channel.send(':x: Filter does not exist.')
        elif 'lock-responses' in command and 'Bot Manager' in roleNames:
            if not len(command.split(' ')) == 2:
                await message.channel.send(':question: `lock-responses` set to `{0}`.'.format(
                    str(self.loader.get_lock_channel_responses())))
                return

            lock = command.split(' ')[1]
            self.loader.set_lock_channel(lock.lower() == 'true')
            await message.channel.send(':white_check_mark: Set `lock-responses` to `{0}`.'.format(
                str(self.loader.get_lock_channel_responses())))
        elif command == 'exit' and 'Bot Manager' in roleNames:
            await message.channel.send(':stop_button: Exiting...')
            await self.logout()
            sys.exit(0)
        elif command == 'custom-responses' and 'Bot Manager' in roleNames:
            if len(self.loader.get_custom_responses()) == 0:
                await message.channel.send(':x: No custom responses set.')
            else:
                out_str = ''
                for key in self.loader.get_custom_responses():
                    out_str += '"' + key + '" -> "' + self.loader.get_custom_responses()[key] + '"\n'
                await message.channel.send(':loudspeaker: Custom responses:\n```{0}```'.format(out_str))
        elif 'add-response' in command and 'Bot Manager' in roleNames:
            if not len(command.split(' ')) >= 3:
                await message.channel.send(':x: Incorrect number of arguments.')
                return

            await message.channel.send(':white_check_mark: Response set.')
            segment = command.split(' ')[1:]
            if ' '.join(segment).count('"') < 4:
                self.loader.add_response(segment[0], segment[1])
            else:
                combined = ' '.join(segment)
                quotes = [combined.split('"')[index] for index in [1, 3]]
                self.loader.add_response(quotes[0][0:len(quotes[0])], quotes[1][0:len(quotes[0])])
        elif 'remove-response' in command and 'Bot Manager' in roleNames:
            if not len(command.split(' ')) >= 2:
                await message.channel.send(':x: Incorrect number of arguments.')
                return

            removal = command.split(' ')[1:]
            full_removal_str = ' '.join(removal)
            if self.loader.remove_response(full_removal_str):
                await message.channel.send(':white_check_mark: Response removed.')
            else:
                await message.channel.send(':x: Response does not exist.')
        elif 'smotm' in command and 'Bot Manager' in roleNames:
            if not len(command.split(' ')) >= 2:
                await message.channel.send(':x: Incorrect number of arguments.')
                return

            motm = command.split(' ')[1:]
            motm_str = ' '.join(motm)
            self.loader.set_motm(motm_str)
            await message.channel.send(':white_check_mark: MOTM set to: {0}'.format(self.loader.get_motm()))
        else:
            await message.channel.send(':question: Command not recognized or insufficient permissions.')

    def set_loader(self, loader: JSONLoader):
        self.loader = loader
        self.prefix = self.loader.get_prefix()


# Check for args
args = sys.argv
argList = args[1:]
unixOptions = 'gt:m:p:'
gnuOptions = ['generate', 'token=', 'motm=', 'prefix=']
try:
    arguments, values = getopt.getopt(argList, unixOptions, gnuOptions)
except getopt.error as err:
    # output error, and return with an error code
    print(str(err))
    sys.exit(2)
generate = False
dataArgs = {}
for currentArg, currentVal in arguments:
    if currentArg in ('-g', '--generate'):
        generate = True
    elif currentArg in ('-t', '--token'):
        dataArgs['token'] = currentVal
    elif currentArg in ('-m', '--motm'):
        dataArgs['motm'] = currentVal
    elif currentArg in ('-p', '--prefix'):
        dataArgs['prefix'] = int(currentVal)

if not path.isfile('config.json'):
    generate = True
data = JSONLoader(dataArgs, generate)

data.load_config()
if data.get_token() == '':
    # Exit if no token found
    print('No token found')
    sys.exit(0)
client = Client()
client.set_loader(data)
client.run(data.get_token())
