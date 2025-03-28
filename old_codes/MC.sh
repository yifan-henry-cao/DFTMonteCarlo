# Input arguments: flag=(LAMMPS or VASP) max_iteration num_cores in_dir run_dir save_iter save_freq T
# 1 flag: determines energy source and how to read them
# 2 max_iteration: maximum number of steps of Monte Carlo cycles
# 3 num_cores: number of cores used for energy evaluation
# 4 in_dir: location of the input structure file
# 5 run_dir: the directory where datafiles are located
# 6 save_dir: the directory to save intermediate structures and MClog
# 7 save_freq: the frequency of saving data
# 8 T: annealing temperature in the Metropolis-Hastings algorithm

#echo $1
#mkdir -p data/run_folder_$2

case $1 in
    LAMMPS)
        echo "LAMMPS active"
        homedir=$(pwd)
        lammps="${HOME}/MD_intro/lammps/src/lmp_mpi"
        FILE=$6MClog
        if [ -f "$FILE" ]; then
            # Restart a run from the last documented step
            echo "$FILE exists, reading last step info"
            read -a strarr <<< $( tail -1 $FILE )
            istart=$((${strarr[0]}))
            python3 /home/yifanc/MC_simulations/util/MC_prep.py $1 $istart $6POSCAR_${istart} $5 1
        else
            # Initialize a fresh run starting from in_dir structure
            echo "$FILE does not exist. Initializing.."
            istart=0
            python3 /home/yifanc/MC_simulations/util/MC_prep.py $1 $istart $4 $5 1
            cd $5
            srun -n $3 ${lammps} -in in.lmp -log none -screen none -var potentials_dir /home/yifanc/MD_intro/potentials
            cd $homedir
            python3 /home/yifanc/MC_simulations/util/MC_fin.py $1 $istart $5 $6 $7 $8 1
        fi

        # Entering main loop
        for ((i=$(($istart+1)); i<$2; i++))
        do
            python3 /home/yifanc/MC_simulations/util/MC_prep.py $1 ${i} $5accepted_POSCAR $5 0
            cd $5
            srun -n $3 ${lammps} -in in.lmp -log none -screen none -var potentials_dir /home/yifanc/MD_intro/potentials
            cd $homedir
            python3 /home/yifanc/MC_simulations/util/MC_fin.py $1 ${i} $5 $6 $7 $8 0
            echo ${i}
        done
        ;;
    VASP)
        echo "VASP active"
        export OMP_NUM_THREADS=1
        homedir=$(pwd)
        vasp_gam="mpirun -np $3 /home/yifanc/MD_intro/vasp.6.2.1/bin/vasp_gam"
        FILE=$6MClog
        if [ -f "$FILE" ]; then
            # Restart a run from the last documented step
            echo "$FILE exists, reading last step info"
            read -a strarr <<< $( tail -1 $FILE )
            istart=$((${strarr[0]}))
            python3 /home/yifanc/MC_simulations/util/MC_prep.py $1 $istart $6POSCAR_${istart} $5 1
        else
            # Initialize a fresh run starting from in_dir structure
            echo "$FILE does not exist. Initializing.."
            istart=0
            python3 /home/yifanc/MC_simulations/util/MC_prep.py $1 $istart $4 $5 1
            cd $5
            $vasp_gam
            cd $homedir
            python3 /home/yifanc/MC_simulations/util/MC_fin.py $1 $istart $5 $6 $7 $8 1
        fi

        # Entering main loop
        for ((i=$(($istart+1)); i<$2; i++))
        do
            python3 /home/yifanc/MC_simulations/util/MC_prep.py $1 ${i} $5accepted_POSCAR $5 0
            cd $5
            $vasp_gam
            cd $homedir
            python3 /home/yifanc/MC_simulations/util/MC_fin.py $1 ${i} $5 $6 $7 $8 0
            echo ${i}
        done
        ;;
    *)
        echo "Unrecognized Flag passed, please indicate energy source!"
        ;;
esac

# if [ $1 = "LAMMPS" ]
# then
#     echo "LAMMPS active"
# elif [ $1 = "VASP" ]
# then
#     echo "VASP active"
# else
#     echo "Unrecognized Flag passed, please indicate energy source!"
# fi