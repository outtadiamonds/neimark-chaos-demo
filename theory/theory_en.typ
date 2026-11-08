#import "style.typ": setup, title, term
#show: setup.with("en")

#title[Neimark oscillator][dynamic chaos and the correlation function]

= What the program shows

The Neimark oscillator is one of the simplest mechanical systems with #term[dynamic chaos]. Its motion is strictly deterministic: the equations contain nothing random. In the mixing regimes H and E considered here, the velocity sequence looks random and its correlation decays; this does not apply to every parameter value or observable.

The "Demonstration" button opens two tabs, selected at the top of the right panel. Blue circles identify the main trajectory or original realization; orange diamonds identify the nearby trajectory or shifted copy. Shapes distinguish them without colour.

== The "Oscillator motion" tab

+ *Mass on a spring.* Position represents displacement, the arrow velocity, and a flash a kick. When the coordinate range expands, the display scale decreases: the mass appearing smaller does not mean a decrease in physical mass or energy.
+ *Phase trajectory $(x,v)$ and velocity $v(t)$.* These are two views of one motion. Between kicks the phase trajectory spirals outwards; at $x=0$ a vertical jump may occur. The horizontal projection connects equal velocities on the two plots.
+ *Half-period map.* The pair $(y_n,y_(n+1))$ lies on one of two branches. The dashed line $y^*=-a\/sqrt(gamma)$ is the switching threshold; $y_n<=y^*$ causes a kick. The lower projection connects the map ordinate to the next sequence value $y_(n+1)$: map → seq.
+ *Nearby trajectories.* Blue circles and orange diamonds compare $y_n$ in the lower sequence plot. There is no separate lower $|Delta y|$ plot. The caption counts half-periods until the first differing "kick / no kick" decision, not loss of all statistical dependence.

*Controls.* H, E, normal mode, and the separate "No kicks" (free) scenario; $v_0$, $epsilon$, animation speed, run/pause, "Step π", reset, projections and $x=0$ markers. Ordinary parameters are constrained to the bounded-motion region (section 5). Manual settings have a small inset from its boundaries to avoid amplification of round-off errors; H and E retain their exact preset parameters. Free illustrates unbounded pumping and stops early before the display leaves a useful range; this software limit is not physical stabilization. For reproducible comparisons choose H or E, select $epsilon$, and reset at $x=0$.

== The "Correlation function" tab

+ *Process.* Samples $y_n$ at $x=0$ form a point process, drawn as vertical stems from zero ending in blue circles. Stems do not describe continuous motion between samples. Continuous mode shows $v(t)$; a dashed line indicates the mean.
+ *Shifted copy.* The same realization at lag $k$ (or $tau$), with orange diamonds. This is not the nearby trajectory from the motion tab.
+ *Overlay.* Products of deviations from the mean are green when positive, red when negative.
+ *Correlation.* The normalized average of products gives $rho(k)$ or $C(tau)/C(0)$. The dashed curve is Markov-partition theory. "Explanation" is the default: the first 6 visible pairs are highlighted sequentially to illustrate the products. These pairs are illustrative only; both modes compute the final estimate from all $N-k$ pairs in the full sample. "Fast" shortens the staged presentation.

*Magnifier.* The top button enables rectangular selection, synchronously changing both $x$ and $y$ ranges of the first three plots: original process, shifted copy and overlay. Ordinate ranges are converted between raw and normalized values. The fourth plot has its own lag axis and is not part of this zoom. "Whole process" resets the selected scale.

*Controls.* Select $y_n$ or $v(t)$, H, E or custom stationary parameters, sample length $N$, "Explanation" / "Fast", run, pause, step, reset and build all lags. Larger $N$ usually reduces scatter of the final estimate. At speed ×1 each lag takes 3 s for shifting, then 2.5 s for highlighting and 2.5 s for showing the product of each of 6 pairs, then 3 s for averaging: 36 s total. Minimum speed is ×0.05. "Step" advances to the next stage, not necessarily the next lag. The parameter and phase planes connect statistics to motion. Transferred parameters are constrained to the stationary region; free is not a stationary correlation experiment.

= Oscillator with negative friction

An #term[oscillator] is a system that oscillates about an equilibrium position. Its state is given by the displacement $x$ and the velocity $v = dot(x)$.

In an ordinary oscillator friction removes energy and the oscillations decay. #term[Negative friction] is a force directed along the velocity: it pumps energy in, as in any generator. The equation without control is
$ dot.double(x) - 2 delta dot(x) + (1 + delta^2) x = 0, quad delta > 0. $
Substituting $x = e^(r t)$ gives $r = delta plus.minus i$, hence
$ x = A_0 e^(delta t) sin(t + phi_0). $
The factor $(1 + delta^2)$ is chosen so that the frequency equals one: the period is $2 pi$ and depends neither on the amplitude nor on $delta$. Over a period the amplitude grows by the factor
$ gamma = e^(2 pi delta) > 1, $
and over a half-period by $sqrt(gamma)$.

== Positive feedback and energy

#term[Positive feedback] is a closed mechanism in which a change in a quantity produces a response that reinforces the original change. "Positive" specifies the reinforcing sign, not a beneficial outcome. Here velocity sets the force $F_("fb")=2 delta v$: $Delta F_("fb")=2 delta Delta v$ acts in the direction of the velocity increment. An external source supplies energy. For $v<0$ the force is negative too, increasing speed rather than necessarily numerical velocity. This is idealized continuous feedback; kicks are separate threshold control.

For unit mass between kicks,
$ E=(v^2+(1+delta^2)x^2)/2. $
Using $dot(x)=v$ and $dot(v)=2 delta v-(1+delta^2)x$ gives
$ dot(E)=v dot(v)+(1+delta^2)x dot(x)
=v(2 delta v-(1+delta^2)x)+(1+delta^2)x v=2 delta v^2>=0. $
Thus $E'=2 delta v^2$ between kicks; energy grows at nonzero velocity and its instantaneous derivative vanishes at a turning point. Energy comes from external pumping.

At a kick $x=0$, $v^(+)=v^(-)-h$, $v^(-)>=a$, hence
$ Delta E=E^(+)-E^(-)=((v^(-)-h)^2-(v^(-))^2)/2=-h v^(-)+h^2/2. $
For $h>0$, energy decreases when $v^(-)>h/2$, is unchanged when $v^(-)=h/2$, and increases when $a<=v^(-)<h/2$. The last case requires $h>2a$, in part of the anomalous regime. For $a=1$, $h=2.6$, $v^(-)=1.1$, one gets $v^(+)=-1.5$ and $Delta E=0.52>0$. Reversal alone does not imply energy loss. Each impulse must not be called an energy dissipator: boundedness depends on the complete map rather than every kick reducing energy.

*Analogies and limits.* An avalanche can entrain more snow; chain-reaction products can initiate more events; income can increase wealth, which can increase future income. These are conditional examples of self-amplification: snow is finite, reaction multiplication depends on the medium, and returns and resources vary. Their mechanisms, randomness and constraints differ from these oscillator equations. Self-amplification does not guarantee chaos: without kicks this linear model has regular exponential growth. Bounded chaotic motion here also requires stretching and threshold return to a bounded region.

*The kick.* To keep the motion bounded an #term[impulse control] is introduced — an instantaneous action at separate moments of time. When the oscillator passes the equilibrium position $x = 0$ with a velocity not less than the critical value $a$, the velocity is instantly reduced by $h$:
$ dot.double(x) - 2 delta dot(x) + (1 + delta^2) x = -h thin theta(dot(x) - a) thin dot(x) thin delta(x). $
Here $theta(z)$ is the Heaviside function (zero for $z < 0$, one for $z >= 0$): it allows a kick only when $dot(x) >= a$. The delta function $delta(x)$ is non-zero only at $x = 0$. At an allowed positive crossing with nonzero velocity, $dot(x) thin delta(x)$ gives a time impulse $delta(t-t_0)$. Its sign differs at a negative crossing, where the Heaviside condition forbids a kick; the equation is interpreted through the event-based velocity jump rule. The factor $h$ is the size of the velocity jump. Below, velocities are measured in units of $a$.

*Dimensionless quantities.* The position $x$, velocity $v$ and time $t$ are dimensionless. Dimensional quantities are $X = L x$, $V = L omega v$, $T = t \/ omega$, where $L$ is a chosen length scale and $omega$ a frequency scale. The model does not fix their numerical values. Velocities are further measured in units of the threshold $a$, i.e. $a = 1$. One half-swing lasts exactly $pi$.

The #term[phase plane] has $x$ on the horizontal axis and $v$ on the vertical one. The state of the oscillator is a point on it, and the motion is drawn as a curve, the #term[phase trajectory]. Negative friction gives an unwinding spiral, and a kick is a vertical jump downwards on the axis $x = 0$ (Fig. 1).

#figure(image("fig_phase.png", width: 58%), caption: [Phase trajectory. The points $y_1, y_2, dots$ are the velocities at the passages of $x = 0$. Red arrows are kicks: the first one reverses the velocity, the second only reduces it.])

= Half-period map

The #term[Poincaré section] is a technique in which, instead of the whole trajectory, one considers only the points where it crosses a chosen line. Here this line is the velocity axis $x = 0$.

Let $y_n$ be the velocity right after the $n$-th passage of $x = 0$ (after the kick, if there was one). There are no kicks until the next passage, and the solution is known exactly:
$ x(u) = y_n e^(delta u) sin u, quad v(u) = y_n f(u), quad 0 <= u < pi, $
where $f(u) = e^(delta u) (delta sin u + cos u)$ is the shape of the velocity over one half-period. At $u = pi$ the oscillator passes $x = 0$ again with the velocity $-sqrt(gamma) y_n$: the velocity has changed sign and grown by the factor $sqrt(gamma)$. Taking the kick into account we obtain a #term[point map] — a rule that gives the next value from the current one:
$ y_(n+1) = -sqrt(gamma) y_n - h thin theta(-sqrt(gamma) y_n - a). $ <map>

#figure(image("fig_map.png", width: 56%), caption: [Graph of the map (@map) at point H. The shaded square is the attractor.])

The graph of the map (Fig. 2) consists of two straight lines with the slope $-sqrt(gamma)$.
- The #term[switching threshold] $y^* = -a \/ sqrt(gamma)$ separates them: the kick condition $-sqrt(gamma) y >= a$ is equivalent to $y <= y^*$. To the left of $y^*$ a kick happens during the half-period, to the right it does not.
- An #term[attractor] is a set that attracts trajectories and that they never leave. Here it is the interval $[-sqrt(gamma) a, a]$. Under section 5 conditions the interval is invariant: pre-kick values range from $a$ to $gamma a$, post-kick values from $a-h$ to $gamma a-h$. The lower edge is the image of the upper one. This does not apply to arbitrary parameters or initial states outside the basin.

= Two modes

The mode is determined by which is larger: the kick $h$ or the threshold $a$.

*Normal mode, $h < a$.* A kick happens at a velocity not less than $a$ and removes less than $a$, so the velocity after the kick stays positive. The kick does not change the direction of motion.

*Anomalous mode, $h > a$.* A kick can remove more than the velocity was, and then the velocity after the kick is negative: the kick reverses the oscillator.

*Signs of neighbouring values.* The swing itself always changes the sign of the velocity: half a period later the oscillator passes $x = 0$ in the opposite direction. A kick is possible only at a positive velocity.
- After a positive $y_n$ the next value is always negative: the oscillator returns with a negative velocity and there is no kick.
- After a negative $y_n$ the velocity at the end of the half-period is $z = -sqrt(gamma) y_n > 0$, and three cases are possible:

#table(
  columns: (auto, auto, auto, auto),
  align: center,
  table.header[*Velocity before the kick*][*Kick*][*Velocity after*][*Sign of $y_(n+1)$*],
  [$z < a$], [no], [$z$], [$+$],
  [$a <= z < h$], [yes], [$z - h < 0$], [$-$],
  [$z >= h$], [yes], [$z - h >= 0$], [$+$],
)

The second row exists only for $h > a$. Therefore in the normal mode the signs alternate strictly, while in the anomalous mode two negative values in a row are possible (but not two positive ones). On the phase plane, after a reversing kick the trajectory stays in the half-plane $x < 0$ (Fig. 1, values $y_1$ and $y_2$).

*What the program implements.* The program is built for the anomalous mode and uses the half-period map, as in [1]. Points H and E lie in the anomalous mode. In the "Custom" mode the normal mode can be selected as well ($gamma < 2$, $h\/a < 1$). There, because of the strict alternation of signs, the half-period sequence contains a non-random component, and $R(k)$ does not decay to zero but keeps changing sign. In the normal mode the decay is observed for the map over a full period.

= Chaos region

The theory holds as long as the motion stays on the interval $[-sqrt(gamma) a, a]$. This gives two conditions on the parameters.

*The kick is not too weak.* Over a full cycle a positive velocity $y$ turns into $gamma y - h$: it grows by the factor $gamma$ and is reduced by $h$. It does not grow if $gamma y - h <= y$, i.e. $y <= h \/ (gamma - 1)$. The largest value on the attractor is $a$, hence
$ h\/a >= gamma - 1. $
Otherwise the pumping is stronger than the kicks and the motion goes to infinity. On the "Oscillator motion" tab this is seen in the "No kicks" scenario ($h = 0$): the spiral unwinds without bound, and the program stops the experiment when the velocity exceeds $10^4$.

*The kick is not too strong.* The lowest value after a kick is $a - h$. It must not fall below the lower edge:
$ a - h >= -sqrt(gamma) a, quad "i.e." quad h\/a <= 1 + sqrt(gamma). $

Together with the condition $gamma > 1$ these inequalities single out the #term[chaos region] $A B C$ on the #term[parameter plane] $(h\/a, gamma)$ (Fig. 3).

#figure(image("fig_plane.png", width: 52%), caption: [Parameter plane. The blue and beige areas together form the chaos region; the beige one is the normal mode.])

The lines on the plane correspond to special coincidences.

#table(
  columns: (auto, auto, 1fr),
  table.header[*Line*][*Equation*][*Meaning*],
  [$A B$], [$h\/a = gamma - 1$], [the lower edge is mapped into the upper edge],
  [$C B$], [$h\/a = 1 + sqrt(gamma)$], [the switching threshold after a kick lands on the lower edge],
  [$A C$], [$gamma = 1$], [no pumping and no chaos],
  [$G D$], [$h\/a = 1$], [boundary of the modes: normal on the left, anomalous on the right],
  [$H C$], [$h\/a = 1 + 1\/sqrt(gamma)$], [the switching threshold after a kick is mapped into itself],
  [$D E$], [$h\/a = gamma$], [the lower edge is mapped into zero],
)

Points H, E and G lie at intersections of these lines: $H = A B inter H C$, $E = D E inter C B$, $G = A B inter G D$.

= Where randomness comes from

#term[Dynamic chaos] is irregular, random-looking behaviour of a system whose equations contain no random quantities.

*Instability.* On each smooth branch $T'(y)=-sqrt(gamma)$. While two trajectories follow the same branches, $|Delta y_n|=epsilon gamma^(n\/2)$ in exact arithmetic. The Lyapunov exponent is $ln sqrt(gamma)=pi delta$ per half-period, or $delta$ per unit time. Reaching scale $L$ takes roughly $n approx ln(L/epsilon)/ln sqrt(gamma)$ steps; $L approx 1$ yields the familiar estimate. This limits pointwise prediction, not calculation of a trajectory or its statistics.

*Threshold and bifurcation.* A #term[bifurcation] is a qualitative change in dynamics as a system parameter varies. Here $y^*=-a\/sqrt(gamma)$ is a #term[switching threshold in state space] at fixed parameters, not a bifurcation parameter value. Lecture notes [5] call this threshold a "bifurcation"; that usage differs from the strict definition. The value $a$ is the pre-kick velocity threshold, while $y^*$ applies to the preceding post-kick sample. Nearby states on opposite sides select different branches; their images approach a separation $h$ in the limit.

*On screen.* Blue circles and orange diamonds initially nearly coincide. After the first differing "kick / no kick" decision the distance formula ceases to apply, but both trajectories remain deterministic. The sequences and map show this without a separate distance plot.

For $epsilon=10^(-8)$ in the agreed demonstration from the initial state, H first differs after 40 half-periods and E after 39: $40 pi approx 125.7$ and $39 pi approx 122.5$ model time units. With one model unit displayed as one second and speed ×4, wall-clock waits are about 31.4 and 30.6 seconds. These counts refer to the chosen initial state and first differing branch decision, not every run. Smaller $epsilon$ postpones the effect logarithmically; demonstrating $10^(-8)$ is feasible. Physical seconds require a frequency scale $omega$: generally $T=n pi/omega$.

*Finite precision.* Analytic motion between events eliminates time-stepping ODE integration error, but floating-point errors remain in exponentials, multiplication and threshold comparisons. Instability may amplify them. The imposed $epsilon$ is a controlled initial difference, not an absence of computational error; exact divergence counts are not universal.

*Boundedness and chaos.* Stretching separates nearby states while threshold kicks return them to an invariant interval in the parameter region considered. The chaotic attractor is called strange in the teaching description; instability without boundedness is insufficient. Exceptional trajectories such as exact rest need not appear chaotic.

*Mixing and ergodicity.* Relative to invariant probability $mu$, #term[mixing] means $mu(A inter T^(-n) B) -> mu(A)mu(B)$: relations between events vanish at large lags. The invariant density need not be uniform. #term[Ergodicity] means no nontrivial invariant sets; time averages of integrable observables equal ensemble averages for almost every initial state. Mixing implies ergodicity, but not conversely. Period-2 cyclic structure may preserve ergodicity of the one-step map while preventing mixing. Zero correlation for one observable does not establish independence or mixing of the whole system.

= Correlation function

Since an individual trajectory cannot be predicted, the process is described statistically. A process is called #term[stationary] if its statistical properties do not change with time. The #term[stationary probability density] $w(y)$ shows how often values near $y$ occur.

The #term[correlation function] shows how strongly the value at a given moment is related to the value $k$ steps later:
$ R(k) = lr(⟨ (y_n - ⟨y⟩)(y_(n+k) - ⟨y⟩) ⟩), quad rho(k) = R(k) \/ R(0). $
The quantity $R(0)$ is the variance. For an ergodic process the ensemble average may be replaced by the time average along one long realization. Both modes compute the final experimental estimate from all $N-k$ full-sample pairs; the first 6 visible pairs in "Explanation" only illustrate the operation:
$ hat(R)(k) = 1/(N-k) sum_(n=1)^(N-k) (y_n - overline(y))(y_(n+k) - overline(y)). $
For sufficiently fast decay of dependence, typical statistical scatter is of order $1 \/ sqrt(N)$. Large lags leave fewer pairs; the 6 illustrative pairs do not replace full-sample averaging. This scaling is not universal.

*Visual meaning.* The realization is copied and shifted by $k$, then laid over the original, and the deviations are multiplied at every point.
- If the copy "resembles" the original, the products are mostly positive and $R(k) > 0$.
- If the copy is "in antiphase", the products are mostly negative.
- If the values separated by the shift $k$ are no longer related, positive and negative contributions cancel and $R(k) approx 0$.

The shift at which the correlation practically vanishes is called the #term[correlation time]. In the mixing regimes H and E discrete-process correlation decays despite deterministic motion. Practical correlation time depends on a tolerance; exponential decay does not mean an exact zero at finite lag. Decay depends on the whole map, not only $sqrt(gamma)$.

= Exact theory: Markov partition

A process is called #term[Markov] if its future depends only on its current state.

The images of the upper edge $a$, of the point $a - h$ (where the switching threshold goes after a kick) and of the lower edge, together with the switching threshold, divide the attractor into intervals. Every half-period new partition points appear. If from some step on no new points appear, we obtain a #term[Markov partition]: each interval $I_alpha$ is mapped linearly and entirely onto a union of several intervals:
$ I_alpha -> union.big_beta d_(alpha beta) I_beta, quad y -> s_alpha y + C_alpha, quad d_(alpha beta) in {0, 1}. $
The matrix $D = ||d_(alpha beta)||$ is the transition matrix. Transitions between the intervals form a Markov chain, With invariant piecewise-constant density, the symbolic sequence of interval labels forms a finite Markov chain. This describes interval transitions, not replacement of all real-valued velocities by finitely many states. Parameter values for which the partition is finite are called #term[Markov points].

The #term[Perron–Frobenius operator] $P$ carries a probability density one step forward:
$ (P rho)(z) = sum_(y: thin T(y) = z) rho(y) \/ |T'(y)|. $
The meaning of the formula: if an interval is stretched by the factor $sqrt(gamma)$, the density on it decreases by the factor $sqrt(gamma)$. The stationary density is piecewise constant: $w(y) = w_alpha$ for $y in I_alpha$. Its values follow from
$ w_beta = sum_alpha d_(alpha beta) w_alpha \/ |s_alpha|, quad sum_alpha w_alpha |I_alpha| = 1. $
The correlation function is expressed through the same operator:
$ lr(⟨ y_0 y_k ⟩) = integral z thin (P^k [y thin w(y)])(z) thin d z. $
The operator $P$ maps functions that are linear on every interval into functions of the same kind. Therefore the calculation reduces to finite recurrence relations for two coefficients per interval. This is equivalent to the recursion for the integrals $U_alpha [k]$, $V_alpha [k]$ in [1].

Markov points provide special parameters with a finite partition in the region considered; finiteness is not assumed for arbitrary parameters. For arbitrary parameters the program builds an _approximate_ Markov partition: new points closer than a given accuracy to existing ones are merged with them. The quality of the approximation can be judged by how well the theoretical curve matches the experiment.

*Point H:* $sqrt(gamma) = (1 + sqrt(5))\/2 approx 1.618$, $h\/a = gamma - 1 approx 1.618$. The partition has two intervals: $I_1 = [-a\/sqrt(gamma), a]$ of length $sqrt(gamma) a$ and $I_2 = [-sqrt(gamma) a, -a\/sqrt(gamma)]$ of length $a$. The interval $I_1$ lies to the right of the switching threshold and is mapped without a kick onto $I_1 union I_2$; the interval $I_2$ gets a kick and is mapped onto $I_1$. From the balance $w_2 = w_1 \/ sqrt(gamma)$ and the normalization we get
$ w_1 = sqrt(gamma)\/(1 + gamma) approx 0.447, quad w_2 = 1\/(1 + gamma) approx 0.276, $
and $rho(1) approx -0.809$, $rho(2) approx 0.573$, $rho(3) approx -0.382$. Asymptotically $rho(k) prop (-1\/sqrt(gamma))^k$: the correlation decays exponentially while changing sign.

*Point E:* $gamma = h\/a approx 2.618$. The lower edge is mapped into zero, and zero is a fixed point of the map. Zero becomes a new partition point, $N = 3$. Here $rho(1) approx rho(2) approx -0.118$, $rho(3) approx 0.146$.

*Point G:* $gamma = 2$, $h\/a = 1$ — on the boundary of the modes. Alternation of period-2 components prevents mixing of the one-step map, and correlation can retain an alternating contribution. This alone does not prove non-ergodicity: the map may interchange components ergodically, while its square acts within each. Full-period decay must account for the selected component and its mean. In the program this point is marked on the parameter plane but has no separate button.

= Continuous process $v(t)$

In the "continuous $v(t)$" mode the velocity is considered at all moments of time, not only at the passages of $x = 0$:
$ v(t) = y_n f(t - n pi) quad "for" quad n pi <= t < (n + 1) pi. $
Every half-period is the same curve $f$ multiplied by its own value $y_n$.

*What is seen on the screen.* Time is measured in units of $pi$: one division is one half-period. The curve $v(t)$ looks like a growing sinusoid with vertical drops at the moments of kicks. The shift $tau$ changes in steps of $pi\/8$. The third plot shades the area under the product of deviations, and the fourth one builds
$ C(tau) = lr(⟨ (v(t) - ⟨v⟩)(v(t + tau) - ⟨v⟩) ⟩). $

*Theory.* For a stationary process the phase within a half-period is uniformly distributed, so for $tau = m pi + r$, $0 <= r < pi$:
$ lr(⟨ v(t) v(t + tau) ⟩) &= 1/pi M_m integral_0^(pi - r) f(u) f(u + r) d u \
  &+ 1/pi M_(m+1) integral_(pi - r)^pi f(u) f(u + r - pi) d u, $
where $M_m = lr(⟨ y_n y_(n+m) ⟩)$ are the moments of the sequence $y_n$ from section 8. The two terms correspond to two cases: the moment $t + tau$ falls into the half-period number $n + m$ or into the next one.

*How to read the result.* $C(tau)$ is a wave with a period of about $2 pi$: at $tau approx pi$ it is negative (half a period later the velocity points the opposite way), at $tau approx 2 pi$ it is positive. The amplitude of the wave first decreases — this part is determined by $R(k)$.

*Why $C(tau)$ does not decay to zero.* The oscillation period does not depend on the amplitude and the kick is instantaneous, so the zero crossings are strictly periodic; only the amplitudes are random. Such a process is called #term[cyclostationary]: its statistics are not constant but repeat with a period. The mean $⟨y⟩$ is not zero because kicks happen only when moving in one direction. Therefore $v(t)$ has a non-random periodic component $⟨y⟩ f(u)$, and $C(tau)$ contains a non-decaying periodic part proportional to $⟨y⟩^2$. The sequence $y_n$ forgets the past completely, whereas the continuous velocity forgets the amplitude but keeps the phase of the oscillations.

= Glossary

#table(
  columns: (auto, 1fr),
  table.header[*Term*][*Definition*],
  [Oscillator], [a system oscillating about an equilibrium position],
  [Negative friction], [a force along the velocity that pumps energy in],
  [$gamma$], [amplitude growth per period, $gamma = e^(2 pi delta)$],
  [Impulse control], [an instantaneous action at separate moments of time (a kick)],
  [Phase plane], [the "position — velocity" plane],
  [Phase trajectory], [the curve traced by the state on the phase plane],
  [Poincaré section], [the points where the trajectory crosses a chosen line],
  [Point map], [the rule $y_(n+1) = T(y_n)$],
  [Attractor], [a set that attracts trajectories],
  [Strange attractor], [an attractor on which the motion is unstable],
  [Switching threshold], [$y^* = -a\/sqrt(gamma)$: a kick to the left of it, none to the right],
  [Bifurcation], [a qualitative change in dynamics as a system parameter varies],
  [Normal and anomalous modes], [$h < a$ and $h > a$: a kick cannot or can reverse the velocity],
  [Chaos region], [parameters for which the motion stays on the attractor],
  [Dynamic chaos], [random-looking behaviour of a deterministic system],
  [Lyapunov exponent], [the rate of divergence of close trajectories, here $ln sqrt(gamma)$],
  [Mixing], [forgetting the initial condition],
  [Ergodicity], [equality of the time average and the ensemble average],
  [Stationary process], [a process with time-independent statistics],
  [Correlation function], [a measure of the relation between values separated by a shift],
  [Correlation time], [the shift after which the relation vanishes],
  [Markov process], [a process whose future depends only on the present],
  [Markov partition], [a division of the attractor into intervals mapped entirely onto one another],
  [Markov point], [parameters for which such a partition is finite],
  [Perron–Frobenius operator], [the rule that carries a probability density one step forward],
  [Cyclostationary process], [a process with statistics periodic in time],
)

= References

+ Stratonovich R. L., Ruzmaikina A. A., Chichigina O. A. Dynamic chaos in an oscillator with negative friction. Anomalous mode \/\/ Radiophysics and Quantum Electronics. 1993. Vol. 36, No. 9. P. 613–622.
+ Neimark Yu. I. Dynamical Systems and Controlled Processes. Moscow: Nauka, 1978 (in Russian).
+ Neimark Yu. I., Landa P. S. Stochastic and Chaotic Oscillations. Moscow: Nauka, 1987 (in Russian).
+ Landa P. S., Stratonovich R. L. Stationary probability distribution for a simplest strange attractor \/\/ Dokl. Akad. Nauk SSSR. 1982. Vol. 267, No. 4.
+ Chichigina O. A. Fluctuation Processes. Lecture notes. Sec. 8.3 "Neimark oscillator", pp. 75–76 (in Russian).
