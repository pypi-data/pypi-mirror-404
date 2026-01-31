class ViolationHandler1:
    """
    Decision structure for :class:`BallComp` algorithm.

    ViolationHandler1 is initialized with a `max balls` and `max radius`
    argument. If BallComp uses this handler, then BallComp will terminate once
    either of the max conditions of this handler is reached.
    """

    def __init__(self,maxBalls,maxRadius):
        self.maxBalls = maxBalls
        self.maxRadius = maxRadius
        return

    def check_violation_1(self,ballRadius, maxBallCompRadius):
        """
        :return: terminate,delta value
        :rtype: bool,float
        """

        if ballRadius >= self.maxRadius - 0.05:
            return (True,None)

        if ballRadius <= maxBallCompRadius:
            return (False,None)

        q = self.maxRadius - maxBallCompRadius
        d = ballRadius - maxBallCompRadius
        return (False,d + (q / 2.0))

    """
    return:
    - (bool::terminate,float::(delta value))
    """
    def check_violation_2(self, numberOfBalls, ballCompMaxBalls):
        ##print("CV {} {} {}".format(numberOfBalls,ballCompMaxBalls, self.maxBalls))

        # case: terminate
        if numberOfBalls > self.maxBalls:
            return (True,None)

        if numberOfBalls <= ballCompMaxBalls:
            return (False,None)

        d = numberOfBalls - ballCompMaxBalls
        ##print("CV2 {} {}".format(numberOfBalls,d))

        # case: spare balls from .`maxBalls`, add 2 extra
        if numberOfBalls + 2 <= self.maxBalls:
            return (False,d + 2)

        # case: spare balls from .`maxBalls`, add 1 extra
        if numberOfBalls + 1 <= self.maxBalls:
            return (False,d + 1)

        # case: no more spare balls
        return (False,d)
