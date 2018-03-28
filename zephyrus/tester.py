import enum
import json
import logging
import multiprocessing
import subprocess
import os
import time
from abc import ABC, abstractmethod

import zmq

from zephyrus.addresses import Participants
from zephyrus.components import ComponentManager
from zephyrus.exceptions import CoreException
from zephyrus.message import Message, Messenger


class TesterMessenger(Messenger):
    no_parameter_messages = {
        'start': 'START',
        'restart': 'RESTART',
        'stop': 'STOP',
    }

    def build_config_message(self, config_data):
        return Message(self.sender, 'CONFIG', config_data)

    def build_result_message(self, result_content):
        return Message(self.sender, 'RESULT', result_content)


# TODO we can do it better,
# TODO find a more suitable place for this
class Mode(enum.Enum):
    CENTRALIZED = 1
    DISTRIBUTED = 2

    @classmethod
    def from_string(cls, name):
        return cls.__members__.get(name)


class Tester(ABC, multiprocessing.Process):
    messenger_class = TesterMessenger

    def __init__(self, simulation_config, run_config, address_config, component_config=None):
        super().__init__()
        self.configs = {}
        self.configs['simulation'] = json.load(open(simulation_config))
        self.configs['run'] = json.load(open(run_config))
        self.participants = Participants(address_config)
        if component_config is not None:
            self.components = ComponentManager(component_config).enum
        self.sockets = {}

    @property
    def messenger(self):
        if getattr(self, '_messenger', None) is None:
            self._messenger = self.messenger_class('tester')
        return self._messenger

    def initialize_participant(self, alias, cmd=None):
        if '<MANUAL>' not in self.configs['run'][alias]:
            # TODO add log
            if cmd is None:
                cmd = self.configs['run'][alias].split()
            # TODO Remove the SHAME!
            os.system(' '.join(cmd) + ' &')
            # subprocess.Popen(cmd)
        else:
            address = self.participants.address(alias)
            logging.info('Run {} manually on {}\n'.format(alias, address))
            input('Press ENTER to continue')
        self.sockets[alias] = self.context.socket(zmq.PUSH)
        self.sockets[alias].connect(self.participants.address(alias))

    def run(self):
        logging.info('conectando...')
        mode = Mode.from_string(self.configs['simulation']['mode'])
        self.context = zmq.Context()
        self.socket_receive = self.context.socket(zmq.PULL)
        self.socket_receive.bind(self.participants.address('tester'))
        if mode == Mode.CENTRALIZED:
            self.initialize_participants_centralized()
        elif mode == Mode.DISTRIBUTED:
            pass
        else:
            raise CoreException("Unknown mode: %s" % mode)
        self.main_loop(mode)
        logging.debug('finalizando os testes...')
        time.sleep(2)

    def initialize_participants_centralized(self):
        # TODO add log
        # plogging.info.plogging.info(self.configs)
        self.initialize_participant('mediator')
        self.initialize_participant('environment')
        self.initialize_participant('agent')
        # TODO fix agent initialization
        """
        for i, cmd in enumerate(self.configs['run']['agents']):
            self.initialize_participant("agent {}".format(i), cmd.split())
        """
        self.initialize_participant('strategy')

    def stop_participants(self):
        stop_message = str(self.messenger.build_stop_message())
        participants = ['strategy', 'mediator', 'environment', 'agent']
        for p in participants:
            self.sockets[p].send_string(stop_message)

    def main_loop(self, mode):
        """
        """
        start_message = str(self.messenger.build_start_message())
        stop_message = str(self.messenger.build_stop_message())

        self.sockets['strategy'].send_string(str(self.build_strategy_config_message()))
        self.sockets['strategy'].send_string(start_message)
        self.sockets['mediator'].send_string(start_message)
        while True:
            logging.debug('waiting message from strategy')
            msg = self.receive_message()
            if msg.sender != 'strategy':
                logging.debug('received message from {} instead of strategy'.format(msg.sender))
                # we shouldn't been receiving messages from any other sender at this point...
                pass
                break
            if msg.type == 'STOP':
                logging.debug('stop participants')
                self.stop_participants()
            elif msg.type == 'EVALUATE':
                logging.debug('evaluate, lets configure environment')
                environ_config = self.build_environment_config_message(msg.content)
                self.sockets['environment'].send_string(str(environ_config))
                self.sockets['environment'].send_string(start_message)
                # TODO this must work for multiple agents
                logging.debug('evaluate, lets configure agent')
                self.sockets['agent'].send_string(str(self.build_environment_config_message()))
                self.sockets['agent'].send_string(start_message)
                # a message from mediator is expected
                logging.debug('evaluate, waiting for mediator\'s answer')
                msg = self.receive_message()

                # TODO check if the message is from mediator or raise error
                # TODO evaluate mediators message
                logging.debug('evaluate, send answer to strategy')
                result_message = self.messenger.build_result_message(msg.content)
                self.sockets['strategy'].send_string(str(result_message))


    def receive_message(self):
        return Message.from_string(self.socket_receive.recv_string())

    def evaluate(self, data):
        pass

    def build_strategy_config_message(self):
        return self.messenger.build_config_message(self.get_strategy_config())

    def get_strategy_config(self):
        return None

    def build_environment_config_message(self, strategy_data):
        return self.messenger.build_config_message(self.get_environment_config(strategy_data))

    def get_environment_config(self):
        return None

    def get_agent_config(self):
        return None

    def get_interaction_config(self):
        return None

    #TODO: expandir para uma versão com roteiro
    def iniciar_simulacao(self, mode):
        teste = self.socket_receive()

        tinicio = time.time()
        logging.debug('Teste iniciado às: ', time.strftime("%H:%M:%S", time.localtime()))
        #self.

        self.configuracao = json.loads(open('configuracao.js').read())
        self.cenario_padrao = map(int, self._configuracao["cenario_padrao"].split())
        self.estrategia = self.estrategia_nsga2()
        populacao = self.estrategia.main_loop()
        self.analise(populacao)

        tfim  = time.time()
        logging.debug('Teste finalizado às: ', time.strftime("%H:%M:%S", time.localtime()))
        logging.debug("tempo consumido: ",  str(tfim - tinicio) + 's')
