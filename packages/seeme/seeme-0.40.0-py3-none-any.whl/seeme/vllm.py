from vllm import LLM, SamplingParams

def default_sampling_params(temperature:float=0.8, top_p:float=0.95):
    return SamplingParams(temperature=temperature, top_p=top_p)

def set_up_vllm(model,tensor_parallel_size, **kwargs):
    llm = LLM(model, tensor_parallel_size, **kwargs)
    return llm

def vllm_generate(llm, prompts, sampling_params=default_sampling_params()):
    return llm.generate(prompts, sampling_params)