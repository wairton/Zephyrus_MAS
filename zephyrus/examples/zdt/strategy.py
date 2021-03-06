import random
import logging

from zephyrus.message import Message
from zephyrus.strategy import Strategy


class ZDTStrategy(Strategy):
    def configure(self, content):
        self.niter = content['niter']
        self.length = content['length']

    def mainloop(self):
        # TODO expecting configuration here?
        best_solution = None
        best_value = None
        for i in range(self.niter):
            logging.info("Strategy: progress {}/{}".format(i + 1, self.niter))
            solution = [random.random() for _ in range(self.length)]
            msg = self.messenger.build_evaluate_message(content={'id': None, 'data': solution})
            self.socket_send.send_string(str(msg))
            ans = Message.from_string(self.socket_receive.recv_string())
            logging.debug('Strategy: received {}'.format(str(ans)))
            value = ans.content['data']
            if ans.type == 'RESULT':
                if best_value is None or best_value > value:
                    best_value = value
                    best_solution = solution
            elif ans.type == 'STOP':
                logging.info('Strategy: stopping.')
                break
        logging.debug('Strategy: best found {}'.format(best_value))
        logging.debug('Strategy: best solution {}'.format(best_solution))
        self.socket_send.send_string(str(self.messenger.build_stop_message()))
        msg = self.messenger.build_result_message(content={
            'value': best_value,
            'solution': best_solution
        })
        logging.debug('Strategy: sending result {}'.format(str(msg)))
        self.socket_send.send_string(str(msg))

if __name__ == '__main__':
    import sys
    ZDTStrategy(*sys.argv[1:]).start()
