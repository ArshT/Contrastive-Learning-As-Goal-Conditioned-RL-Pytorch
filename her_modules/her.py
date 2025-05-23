import numpy as np


class her_sampler:
    def __init__(self, replay_strategy, replay_k, reward_func=None, labelling_strategy="proximity"):
        self.replay_strategy = replay_strategy
        self.replay_k = replay_k
        if self.replay_strategy == "future":
            self.future_p = 1 - (1.0 / (1 + replay_k))
        else:
            self.future_p = 0
        self.reward_func = reward_func

        self.labelling_strategy = labelling_strategy

    def sample_her_transitions(self, episode_batch, batch_size_in_transitions):
        T = episode_batch["actions"].shape[1]
        rollout_batch_size = episode_batch["actions"].shape[0]
        batch_size = batch_size_in_transitions
        # select which rollouts and which timesteps to be used
        episode_idxs = np.random.randint(0, rollout_batch_size, batch_size)
        t_samples = np.random.randint(T, size=batch_size)
        transitions = {
            key: episode_batch[key][episode_idxs, t_samples].copy()
            for key in episode_batch.keys()
        }
        # her idx
        her_indexes = np.where(np.random.uniform(size=batch_size) < self.future_p)
        future_offset = np.random.uniform(size=batch_size) * (T - t_samples)
        future_offset = future_offset.astype(int)
        future_t = (t_samples + 1 + future_offset)[her_indexes]
        # replace go with achieved goal
        future_ag = episode_batch["ag"][episode_idxs[her_indexes], future_t]
        transitions["g"][her_indexes] = future_ag
        
        
        # to get the params to re-compute reward
        if self.labelling_strategy == "proximity":
            dist = np.linalg.norm(transitions['ag_next'] -  transitions['g'],axis=1)
            
            r = dist.copy()
            r[dist < 0.05] = 1
            r[dist >= 0.05] = 0

            r = r.reshape(-1,1)
            transitions['r'] = r
            

        elif self.labelling_strategy == "equal":
            # is_success = (achieved_goal == goal).all(axis=-1)
            is_success = np.all(transitions["ag_next"] == transitions["g"], axis=1)
            is_success = is_success.reshape(-1, 1)
            transitions["r"] = is_success.astype(np.float32)
        

        transitions = {
                k: transitions[k].reshape(batch_size, *transitions[k].shape[1:])
                for k in transitions.keys()
            }

        return transitions
