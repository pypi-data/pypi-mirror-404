__version__ = '0.2.1'
__all__ = [ ]


def demo():
    import numpy as np
    from zdev.display import qplot, plt

    print("Welcome to a little demo for the 'zdev' package!\n")

    tmp = input("Please enter some numbers (separated by ','): \n") 
    x = np.array(str(tmp).split(','), dtype=np.float64)

    qplot(x, info='what-u-just-entered', bold=True)
    plt.show()
    print("")
  
    print("See how quickly things can be plotted by using 'zdev.display.qplot'?")
    print("Have fun! ;)")
    return
