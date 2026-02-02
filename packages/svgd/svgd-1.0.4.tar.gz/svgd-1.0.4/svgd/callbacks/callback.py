from svgd.states import (
    StateOnInitializationDone,
    StateOnSamplingIterationStarted,
    StateOnScoreComputed,
    StateOnProposalComputed,
    StateOnSamplingIterationDone,
    StateOnSamplingDone,
)


class Callback:
    def on_initialization_done(self, state: StateOnInitializationDone):
        pass

    def on_sampling_iteration_started(self, state: StateOnSamplingIterationStarted):
        pass

    def on_score_computed(self, state: StateOnScoreComputed):
        pass

    def on_proposal_computed(self, state: StateOnProposalComputed):
        pass

    def on_sampling_iteration_done(self, state: StateOnSamplingIterationDone):
        pass

    def on_sampling_done(self, state: StateOnSamplingDone):
        pass
