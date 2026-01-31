class LSystem:
    """
    A Lindenmayer System (L-System) string rewriting engine.
    Used for generating fractal curves and organic structures via turtle graphics.
    """
    def __init__(self, axiom: str, rules: dict):
        """
        Initialize the L-System.
        :param axiom: The starting string (e.g., "F").
        :param rules: A dictionary mapping predecessor chars to successor strings.
                      Example: {'F': 'F[+F]F[-F]'}
        """
        self.axiom = axiom
        self.rules = rules
        self.current_string = axiom
        self.iteration_count = 0

    def iterate(self, n: int = 1):
        """
        Apply the rewriting rules n times in parallel.
        """
        for _ in range(n):
            next_string = []
            for char in self.current_string:
                # Apply rule if it exists, otherwise keep character
                successor = self.rules.get(char, char)
                next_string.append(successor)
            self.current_string = "".join(next_string)
            self.iteration_count += 1
        return self.current_string

    def get_result(self):
        """Returns the current string state."""
        return self.current_string

    def reset(self):
        """Resets the L-System to its axiom state."""
        self.current_string = self.axiom
        self.iteration_count = 0