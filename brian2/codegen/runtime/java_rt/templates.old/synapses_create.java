{% macro main() %}
    // USE_SPECIFIERS { _synaptic_pre, _synaptic_post, _post_synaptic,
    //                  _pre_synaptic, _num_source_neurons, _num_target_neurons,
    //                  rand}

    //// SUPPORT CODE //////////////////////////////////////////////////////////
	{% for line in support_code_lines %}
	// {{line}}
	{% endfor %}

	srand((unsigned int)time(NULL));
	int _buffer_size = 1024;
	int[] _prebuf = new int[_buffer_size];
	int[] _postbuf = new int[_buffer_size];
	int[] _synprebuf = new int[1];
	int[] _synpostbuf = new int[1];
	int _curbuf = 0;
	int _synapse_idx = _synaptic_pre.size();
	for(int i=0; i<_num_source_neurons; i++)
	{
		for(int j=0; j<_num_target_neurons; j++)
		{
		    final int _vectorisation_idx = j;
			// Define the condition
			{% for line in code_lines %}
			{{line}}
			{% endfor %}
			// Add to buffer
			if(_cond)
			{
			    if (_p != 1.0) {
			        // We have to use _rand instead of rand to use our rand
                                // function, not the one from the C standard library
                                if (_rand(_vectorisation_idx) >= _p)
                                    continue;
                            }

                            for (int _repetition=0; _repetition<_n; _repetition++) {
                                _prebuf[_curbuf] = i;
                                _postbuf[_curbuf] = j;
                                _curbuf++;
                                // Flush buffer
                                if(_curbuf==_buffer_size)
                                {
                                    _flush_buffer(_prebuf, _synaptic_pre, _curbuf);
                                    _flush_buffer(_postbuf, _synaptic_post, _curbuf);
                                    _curbuf = 0;
                                }
                                // Directly add the synapse numbers to the neuron->synapses
                                // mapping
                                //
                                // TODO: Recheck this especially
                                _synprebuf[0] = _synapse_idx;
                                _synpostbuf[0] = _synapse_idx;
                                ArrayList<Integer> _pre_synapses = new ArrayList<Integer>();
                                _pre_synapses.add(_pre_synaptic[i]);
                                ArrayList<Integer> _post_synapse = new ArrayList<Integer>();
                                _post_synapses.add(_post_synaptic[j]);
                                _flush_buffer(_synprebuf, _pre_synapses, 1);
                                _flush_buffer(_synpostbuf, _post_synapses, 1);
                                _synapse_idx++;
                            }
                        }
                }

        }
	// Final buffer flush
	_flush_buffer(_prebuf, _synaptic_pre, _curbuf);
	_flush_buffer(_postbuf, _synaptic_post, _curbuf);
	delete [] _prebuf;
	delete [] _postbuf;
	delete [] _synprebuf;
	delete [] _synpostbuf;
{% endmacro %}

{% macro support_code() %}
// Flush a buffered segment into a dynamic array
void _flush_buffer(int[] buf, ArrayList<Integer> data, int N)
{
	// Copy the values across
	for(int i=0; i<N; i++)
	{
		data.add(buf[i]);
	}
}

//// SUPPORT CODE //////////////////////////////////////////////////////////
{% for line in support_code_lines %}
{{line}}
{% endfor %}

{% endmacro %}



