UP = 1
DOWN = 2
FLOOR_COUNT = 6

class ElevatorLogic(object):
    """
    An incorrect implementation. Can you make it pass all the tests?

    Fix the methods below to implement the correct logic for elevators.
    The tests are integrated into `README.md`. To run the tests:
    $ python -m doctest -v README.md

    To learn when each method is called, read its docstring.
    To interact with the world, you can get the current floor from the
    `current_floor` property of the `callbacks` object, and you can move the
    elevator by setting the `motor_direction` property. See below for how this is done.
    """

    def __init__(self):
        # Feel free to add any instance variables you want.
        self._callbacks = None
        self._next_floor = None
        self.queue = {}

    def init_floors(self):
        starting_floor = self.callbacks.current_floor
        self.floors = {}
        for i in range(FLOOR_COUNT):
            i += starting_floor
            self.floors[i] = Floor(self, i)

    @property
    def callbacks(self):
        return self._callbacks
    @callbacks.setter
    def callbacks(self, value):
        self._callbacks = value
        self.init_floors()

    @property
    def motor_direction(self):
        return self.callbacks.motor_direction
    @motor_direction.setter
    def motor_direction(self, value):
        if value is None:
            self._next_floor = None
        self.callbacks.motor_direction = value

    @property
    def next_floor(self):
        next_floor = self._next_floor
        if next_floor is None:
            next_floor = self._next_floor = self.find_next_stop()
        return next_floor

    def on_called(self, floor, direction):
        """
        This is called when somebody presses the up or down button to call the elevator.
        This could happen at any time, whether or not the elevator is moving.
        The elevator could be requested at any floor at any time, going in either direction.

        floor: the floor that the elevator is being called to
        direction: the direction the caller wants to go, up or down
        """
        f = self.floors[floor]
        if direction == UP:
            f.called_going_up = True
        elif direction == DOWN:
            f.called_going_down = True

    def on_floor_selected(self, floor):
        """
        This is called when somebody on the elevator chooses a floor.
        This could happen at any time, whether or not the elevator is moving.
        Any floor could be requested at any time.

        floor: the floor that was requested
        """
        self.floors[floor].selected_from_cabin = True

    def on_floor_changed(self):
        """
        This lets you know that the elevator has moved one floor up or down.
        You should decide whether or not you want to stop the elevator.
        """
        current_floor = self.callbacks.current_floor
        should_stop = self.floors[current_floor].on_arrival()
        if should_stop:
            self.motor_direction = None

    def on_ready(self):
        """
        This is called when the elevator is ready to go.
        Maybe passengers have embarked and disembarked. The doors are closed,
        time to actually move, if necessary.
        """
        current_floor = self.callbacks.current_floor
        next_floor = self.next_floor
        if next_floor is None:
            direction = None
        elif next_floor.index > current_floor:
            direction = UP
        elif next_floor.index < current_floor:
            direction = DOWN
        self.motor_direction = direction

    def iter_queue(self):
        for i in sorted(self.queue.keys())[:]:
            yield i, self.queue[i]

    def update_queue(self, floor, value, mode=None, remove_all=False):
        if value:
            add_to_queue = floor not in [r.floor for r in self.queue.values()]
            if not add_to_queue:
                for i, r in self.iter_queue():
                    if r.floor is not floor:
                        continue
                    if r.direction is None:
                        continue
                    if mode is not None and mode == r.direction:
                        continue
                    add_to_queue = True
                    break
            if add_to_queue:
                if not len(self.queue):
                    i = 0
                else:
                    i = max(self.queue.keys()) + 1
                request = FloorRequest(floor, mode, i)
                self.queue[i] = request
                self._next_floor = None
        else:
            removed = False
            for i, r in self.iter_queue():
                if r.floor is not floor:
                    continue
                if remove_all:
                    del self.queue[i]
                    continue
                if r.direction is None:
                    del self.queue[i]
                    self._next_floor = None
                elif r.direction == mode and not removed:
                    del self.queue[i]
                    removed = True
                    self._next_floor = None

    def find_next_stop(self):
        if not len(self.queue):
            return None
        direction = self.motor_direction
        current_floor = self.callbacks.current_floor
        next_floor = None
        for i, r in self.iter_queue():
            if direction is None:
                if r.floor == current_floor:
                    return r.floor
                if next_floor is None or r.floor < next_floor:
                    next_floor = r.floor
                continue
            if r.floor < current_floor:
                continue
            if next_floor is None or r.floor < next_floor:
                next_floor = r.floor
        return next_floor


class Floor(object):
    def __init__(self, elevator_logic, index):
        self.elevator_logic = elevator_logic
        self.index = index
        self._selected_from_cabin = False
        self._called_going_up = False
        self._called_going_down = False

    @property
    def elevator_floor(self):
        return self.elevator_logic.callbacks.current_floor
    @property
    def elevator_direction(self):
        return self.elevator_logic.motor_direction

    @property
    def queued(self):
        q = (self.called_going_up or
                self.called_going_down or
                    self.selected_from_cabin)
        return q
    @queued.setter
    def queued(self, value):
        attrs = ['selected_from_cabin', 'called_going_up', 'called_going_down']
        for attr in attrs:
            setattr(self, ''.join(['_', attr]), value)
        self.elevator_logic.update_queue(self, False, remove_all=True)

    @property
    def selected_from_cabin(self):
        return self._selected_from_cabin
    @selected_from_cabin.setter
    def selected_from_cabin(self, value):
        if value == self.selected_from_cabin:
            return
        self._selected_from_cabin = value
        self.elevator_logic.update_queue(self, value)

    @property
    def called_going_up(self):
        return self._called_going_up
    @called_going_up.setter
    def called_going_up(self, value):
        if value == self.called_going_up:
            return
        self._called_going_up = value
        self.elevator_logic.update_queue(self, value, UP)

    @property
    def called_going_down(self):
        return self._called_going_down
    @called_going_down.setter
    def called_going_down(self, value):
        if value == self.called_going_down:
            return
        self._called_going_down = value
        self.elevator_logic.update_queue(self, value, DOWN)

    def on_arrival(self):
        floors = self.elevator_logic.floors
        should_stop = False
        if self.selected_from_cabin:
            self.selected_from_cabin = False
            should_stop = True
        direction = self.elevator_direction
        if direction == UP:
            if self.called_going_up:
                self.called_going_up = False
                should_stop = True
            elif self.called_going_down:
                other_floors = [floors[k] for k in floors if k > self.index]
                for floor in other_floors:
                    if floor.queued:
                        break
                    self.called_going_down = False
                    should_stop = True
        elif direction == DOWN:
            if self.called_going_down:
                self.called_going_down = False
                should_stop = True
            elif self.called_going_up:
                other_floors = [floors[k] for k in floors if k < self.index]
                for floor in other_floors:
                    if floor.queued:
                        break
                    self.called_going_up = False
                    should_stop = True
        return should_stop

    def __cmp__(self, other):
        if not isinstance(other, Floor):
            other = self.elevator_logic.floors[other]
        if self.index == other.index:
            return 0
        direction = self.elevator_direction
        current_floor = self.elevator_floor
        if direction is None:
            if self.index == current_floor:
                return 0
            if self.index > current_floor:
                my_diff = self.index - current_floor
            else:
                my_diff = current_floor - self.index
            if other.index > current_floor:
                other_diff = other.index - current_floor
            else:
                other_diff = current_floor - other.index
            if my_diff > other_diff:
                return 1
            return -1
        if direction == UP:
            if self.index < other.index:
                return 1
            return -1
        elif direction == DOWN:
            if self.index > other.index:
                return -1
            return 1

    def __repr__(self):
        return 'Floor {0}'.format(self.index)

    def __str__(self):
        return str(self.index)

class FloorRequest(object):
    def __init__(self, floor, direction, request_index):
        self.floor = floor
        self.direction = direction
        self.request_index = request_index
