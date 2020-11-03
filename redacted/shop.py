import game
import datetime
import redacted.misc_utilities as utils
from UI.colored_text import ColorString
import random

class ShopItem():
    def __init__(self, name=None, cost=0, amount=1):
        self.name = name
        self.cost = cost
        self.amount = amount

class CartItem():
    def __init__(self, item=None, amount=1):
        self.item=item
        self.amount=amount


class MainRoom(game.Location):
    def __init__(self, name='Inconvenience store'):
        super().__init__(name=name)

        self.cart_contents = []
        self.items = {
            'Instant noodles':ShopItem(name='Instant noodles', cost=5, amount=1),
            'Instant soup':ShopItem(name='Instant soup', cost=20, amount=3),
            'Bread':ShopItem(name='Bread', cost=8, amount=1)
        }

        self.in_stock = {self.items['Instant noodles']:0, self.items['Instant soup']:0, self.items['Bread']:0}
        self.oldseed = 0


        @self.object('shelves')
        def shelves():
            pass

        @shelves.action(name='Instant noodles', description='Add Instant noodles (5c) to your cart', time_cost=datetime.timedelta(seconds=10), energycost=game.EnergyCost.NONE, priority=10, color='yellow')
        def add_instant_noodles():
            item = self.items['Instant noodles']
            self.add_item_to_cart(item, 1)
        @shelves.action(name='Instant soup', description='Add Instant soup (20c, pack of 3) to your cart', time_cost=datetime.timedelta(seconds=10), energycost=game.EnergyCost.NONE, priority=11, color='yellow')
        def add_instant_soup():
            item = self.items['Instant soup']
            self.add_item_to_cart(item, 1)
        @shelves.action(name='Bread', description='Add Bread (8c) to your cart', time_cost=datetime.timedelta(seconds=10), energycost=game.EnergyCost.NONE, priority=12, color='yellow')
        def add_bread():
            item = self.items['Bread']
            self.add_item_to_cart(item, 1)
        @shelves.action(name='Remove Instant noodles', description='Remove Instant noodles from your cart', time_cost=datetime.timedelta(seconds=10), energycost=game.EnergyCost.NONE, priority=20, disabled=True, color='yellow')
        def remove_instant_noodles():
            item = self.items['Instant noodles']
            self.add_item_to_cart(item, -1)
        @shelves.action(name='Remove Instant soup', description='Remove Instant soup from your cart', time_cost=datetime.timedelta(seconds=10), energycost=game.EnergyCost.NONE, priority=21, disabled=True, color='yellow')
        def remove_instant_soup():
            item = self.items['Instant soup']
            self.add_item_to_cart(item, -1)
        @shelves.action(name='Remove Bread', description='Remove Bread from your cart', time_cost=datetime.timedelta(seconds=10), energycost=game.EnergyCost.NONE, priority=22, disabled=True, color='yellow')
        def remove_bread():
            item = self.items['Bread']
            self.add_item_to_cart(item, -1)

        @shelves.action(name='check cart contents', description='Check the contents of your shopping cart', time_cost=datetime.timedelta(seconds=30), energycost=game.EnergyCost.MENTAL, priority=30, color='yellow')
        def check_cart_contents():
            self.show_cart_contents(30)

        @shelves.action(name='checkout', description='Purchase the contents of your shopping cart', time_cost=datetime.timedelta(minutes=3), energycost=game.EnergyCost.LIGHT, priority=31, color='yellow')
        def checkout():
            total_cost = 0
            for thing in self.cart_contents:
                total_cost += thing.item.cost*thing.amount
            money = game.game_state.get_stat('money')
            if total_cost > money:
                game.show_message('Your total is {}c. Unfortunately you do not have enough money.'.format(total_cost))
                return
            money -= total_cost
            game.game_state.set_stat('money', money)
            for thing in self.cart_contents:
                for i in range(thing.amount*thing.item.amount):
                    utils.add_to_inventory(thing.item.name)
            game.show_message('Your total is {}c. You take the items you bought with you.'.format(total_cost))

            self.cart_contents = []
            for item in self.items:
                shelves.get_action('Remove ' + item).disable()

    def add_item_to_cart(self, item, amount):
        in_cart = False
        for thing in self.cart_contents:
            if thing.item == item:
                in_cart = True
                thing.amount += amount
                if thing.amount == 0:
                    self.cart_contents.remove(thing)
                    self.get_object('shelves').get_action('Remove ' + item.name).disable()
                else:
                    self.get_object('shelves').get_action('Remove ' + item.name).enable()
                break
        if not in_cart:
            self.cart_contents.append(CartItem(item))
            self.get_object('shelves').get_action('Remove ' + item.name).enable()
        self.in_stock[item] += -amount

        if self.in_stock[item]:
            self.get_object('shelves').get_action(item.name).enable()
        else:
            self.get_object('shelves').get_action(item.name).disable()

        if amount >= 0:
            game.show_message('You add the {} to your shopping cart.'.format(item.name))
        else:
            game.show_message('You remove the {} from your shopping cart.'.format(item.name))

    def show_cart_contents(self, width=30):
        if len(self.cart_contents) == 0:
            game.show_message('There is nothing in your shopping cart.')
            return
        total_cost = 0
        message = 'In your shopping cart, there is:\n'
        for thing in self.cart_contents:
            m_start = '{}× {} '.format(thing.amount, thing.item.name)
            m_end = ' {}\n'.format(thing.item.cost*thing.amount)
            message += m_start + (width - len(m_start) - len(m_end))*'.' + m_end
            total_cost += thing.item.cost*thing.amount
        m_start = 'Total: '
        m_end = ' {}\n'.format(total_cost)
        message += m_start + '_'*(width - len(m_start) - len(m_end)) + m_end
        game.show_message(message)

    def restock(self):
        seed = game.game_state.get_stat('seed')
        if seed == self.oldseed:
            return

        random.seed(a=seed)
        for thing in self.in_stock:
            self.in_stock[thing] = random.randrange(1, 16)

    def when_entering(self, from_location):
        self.restock()
        game.game_state.location = self


class StorageRoom(game.Location):
    def __init__(self, name='Storage room'):
        super().__init__(name=name)

        @self.object('storage shelves')
        def storage_shelves():
            pass

        self.get_object('storage shelves').glasses = game.Alignment.INDEPENDENT

        @storage_shelves.action('Switch glasses', time_cost=datetime.timedelta(seconds=15), energycost=game.EnergyCost.NONE, color='cyan', disabled=True)
        def switch_glasses():
            glasses = self.glasses
            m_start = ('You put the glasses on. You leave your old ones in their place.', 'white')

            if storage_shelves.glasses == game.Alignment.INDEPENDENT:
                if glasses == game.Alignment.GOVERNMENT:
                    game.show_message(ColorString(m_start, (' Everything changes colours. They are not tinted red like your previous ones.', 'cyan')))
                else:
                    game.show_message(ColorString(m_start))
            else:
                if glasses == game.Alignment.INDEPENDENT:
                    game.show_message(ColorString(m_start, (' Everything goes back to normal. This is how it was always supposed to be.', 'red')))
                else:
                    game.show_message(ColorString(m_start))

            self.glasses = storage_shelves.glasses
            storage_shelves.glasses = glasses
            self.glasses_on()
            if storage_shelves.glasses == game.Alignment.GOVERNMENT:
                storage_shelves.get_action('Switch glasses').color = 'red'
            else:
                storage_shelves.get_action('Switch glasses').color = 'cyan'

        @self.action('Remove Lens', time_cost=datetime.timedelta(seconds=30))
        def remove_lens():
            self.glasses_off()

        @self.action('Equip Lens', time_cost=datetime.timedelta(seconds=30), disabled=True, color='yellow')
        def equip_lens():
            self.glasses_on()

    def glasses_off(self):
        self.glasses = game.game_state.glasses.type
        game.game_state.glasses.type = game.Alignment.INDEPENDENT
        self.get_action('Travel to Inconvenience store').disable()
        self.get_action('Equip Lens').enable()
        if self.glasses == game.Alignment.GOVERNMENT:
            self.get_action('Equip Lens').color = 'yellow'
        else:
            self.get_action('Equip Lens').color = 'white'
        self.get_action('Remove Lens').disable()
        self.get_object('storage shelves').get_action('Switch glasses').enable()

    def glasses_on(self):
        game.game_state.glasses.type = self.glasses
        self.glasses = None
        self.get_action('Travel to Inconvenience store').enable()
        self.get_action('Remove Lens').enable()
        self.get_action('Equip Lens').disable()
        self.get_object('storage shelves').get_action('Switch glasses').disable()


    def when_entering(self, from_location):
        self.glasses = None
        if game.game_state.get_stat('truth'): #and > potrebne
            self.get_action('Remove Lens').enable()
        else:
            self.get_action('Remove Lens').disable()

        game.game_state.location = self


class Office(game.Location):
    def __init__(self, name='Office'):
        super().__init__(name=name)

        global job
        job = False


        @self.object('manager')
        def manager():
            pass

        @manager.action('Apply', description='Apply for a job as a cashier', time_cost=datetime.timedelta(minutes=30), energycost=game.EnergyCost.MENTAL, color='yellow')
        def apply():
            job = True
            self.get_action('Travel to Staff room').enable()
            apply.disable()

        @manager.action('Leave job', description='Leave your job as a cashier')
        def leave_job():
            pass


class StaffRoom(game.Location):
    def __init__(self, name='Staff room'):
        super().__init__(name=name)


main_room = MainRoom()
office = Office()
storage_room = StorageRoom()
staff_room = StaffRoom()

main_room.add_neighbor(office, timecost=datetime.timedelta(minutes=2))
main_room.add_neighbor(storage_room, timecost=datetime.timedelta(minutes=1))
office.add_neighbor(staff_room, timecost=datetime.timedelta(seconds=20))
office.get_action('Travel to Staff room').disable()
